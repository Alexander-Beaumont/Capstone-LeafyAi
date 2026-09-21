from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction, SafetyCheck
from ai_agent.providers import get_provider, get_vlm_provider
from ai_agent.serializers import AIConfigurationSerializer, AIDecisionSerializer, AIRecommendationRunSerializer, FarmActionSerializer, SafetyCheckSerializer
from ai_agent.services import NoDeviceError, RecommendationGenerationError, _read_images, generate_recommendation, latest_image_candidates
from telemetry.models import Farm, FarmDevice


class AIDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIDecision.objects.select_related("safetycheck", "run").prefetch_related("actions").order_by("-created_at", "-id")
    serializer_class = AIDecisionSerializer


class FarmActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FarmAction.objects.order_by("-id")
    serializer_class = FarmActionSerializer


class SafetyCheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SafetyCheck.objects.order_by("-checked_at", "-id")
    serializer_class = SafetyCheckSerializer


def _farm(farm_id): return get_object_or_404(Farm, id=farm_id)


@api_view(["GET", "PATCH"])
def farm_settings(request, farm_id):
    configuration, _ = AIConfiguration.objects.get_or_create(farm=_farm(farm_id))
    if request.method == "GET": return Response(AIConfigurationSerializer(configuration).data)
    serializer = AIConfigurationSerializer(configuration, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True); serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
def test_provider(request, farm_id):
    farm = _farm(farm_id)
    configuration, _ = AIConfiguration.objects.get_or_create(farm=farm)
    role = request.data.get("role")
    try:
        if role == "llm":
            provider = get_provider(configuration)
            output = provider.complete("Reply with OK only.", "Connection test.")
        elif role == "vlm":
            images = [image for image in latest_image_candidates(farm) if image.vlm_ready][:1]
            readable, failures = _read_images(images)
            if not readable: return Response({"detail": "A reliable readable farm image is required.", "failures": failures}, status=status.HTTP_400_BAD_REQUEST)
            provider = get_vlm_provider(configuration)
            output = provider.complete("Describe the image briefly.", "Connection test.", images=readable)
        else:
            return Response({"detail": "role must be 'llm' or 'vlm'."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response({"success": False, "detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response({"success": True, "provider": provider.provider_name, "model": provider.model_name, "response": str(output)[:500]})


def _generate(farm, device=None):
    try:
        return Response(generate_recommendation(farm, device=device), status=status.HTTP_201_CREATED)
    except NoDeviceError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except RecommendationGenerationError as exc:
        payload = {"error": str(exc)}
        if exc.run: payload["run"] = AIRecommendationRunSerializer(exc.run).data
        return Response(payload, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
def generate_for_farm(request, farm_id):
    farm = _farm(farm_id)
    device = get_object_or_404(FarmDevice, id=request.data["device_id"], farm=farm) if request.data.get("device_id") is not None else None
    return _generate(farm, device)


@api_view(["GET"])
def latest_recommendations(request, farm_id):
    run = AIRecommendationRun.objects.filter(farm=_farm(farm_id)).first()
    if run is None: return Response({"detail": "No recommendation run exists for this farm."}, status=status.HTTP_404_NOT_FOUND)
    return Response(AIRecommendationRunSerializer(run, context={"request": request}).data)


@api_view(["GET"])
def recent_recommendations(request, farm_id):
    runs = AIRecommendationRun.objects.filter(farm=_farm(farm_id))[:3]
    return Response(AIRecommendationRunSerializer(runs, many=True, context={"request": request}).data)


@api_view(["POST"])
def recommend(request):
    if request.data.get("farm_id") is None: return Response({"error": "farm_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    farm = _farm(request.data["farm_id"])
    device = get_object_or_404(FarmDevice, id=request.data["device_id"], farm=farm) if request.data.get("device_id") is not None else None
    return _generate(farm, device)
