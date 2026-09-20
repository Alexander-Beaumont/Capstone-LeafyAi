from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ai_agent.actuators import read_actuator
from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction, KasaActuator, SafetyCheck
from ai_agent.providers import get_provider, get_vlm_provider
from ai_agent.serializers import AIConfigurationSerializer, AIDecisionSerializer, AIRecommendationRunSerializer, FarmActionSerializer, KasaActuatorSerializer, SafetyCheckSerializer
from ai_agent.services import NoDeviceError, RecommendationGenerationError, _read_images, generate_recommendation, latest_images_for_farm
from telemetry.models import Farm, FarmDevice


class AIDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIDecision.objects.select_related("safetycheck", "run").prefetch_related("actions").order_by("-created_at", "-id")
    serializer_class = AIDecisionSerializer


class FarmActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FarmAction.objects.select_related("actuator").order_by("-id")
    serializer_class = FarmActionSerializer


class SafetyCheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SafetyCheck.objects.order_by("-checked_at", "-id")
    serializer_class = SafetyCheckSerializer


def _farm(farm_id):
    return get_object_or_404(Farm, id=farm_id)


@api_view(["GET", "PATCH"])
def farm_settings(request, farm_id):
    farm = _farm(farm_id)
    configuration, _ = AIConfiguration.objects.get_or_create(farm=farm)
    if request.method == "GET":
        return Response(AIConfigurationSerializer(configuration).data)
    serializer = AIConfigurationSerializer(configuration, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
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
            images = latest_images_for_farm(farm, 1)
            readable, failures = _read_images(images)
            if not readable:
                return Response({"detail": "A readable farm image is required to test the VLM.", "failures": failures}, status=status.HTTP_400_BAD_REQUEST)
            provider = get_vlm_provider(configuration)
            output = provider.complete("Describe the supplied image in one short sentence.", "Connection test.", images=readable)
        else:
            return Response({"detail": "role must be 'llm' or 'vlm'."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response({"success": False, "detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response({"success": True, "provider": provider.provider_name, "model": provider.model_name, "response": str(output)[:500]})


@api_view(["GET", "POST"])
def actuator_collection(request, farm_id):
    farm = _farm(farm_id)
    if request.method == "GET":
        return Response(KasaActuatorSerializer(farm.kasa_actuators.all(), many=True).data)
    serializer = KasaActuatorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(farm=farm)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def actuator_detail(request, farm_id, actuator_id):
    actuator = get_object_or_404(KasaActuator, id=actuator_id, farm_id=farm_id)
    if request.method == "DELETE":
        actuator.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = KasaActuatorSerializer(actuator, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
def test_actuator(request, farm_id, actuator_id):
    actuator = get_object_or_404(KasaActuator, id=actuator_id, farm_id=farm_id)
    try:
        state_value = read_actuator(actuator)
    except Exception as exc:
        return Response({"success": False, "detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response({"success": True, "actuator_id": actuator.id, "state": state_value})


def _generate(farm, device=None):
    try:
        return Response(generate_recommendation(farm, device=device), status=status.HTTP_201_CREATED)
    except NoDeviceError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except RecommendationGenerationError as exc:
        payload = {"error": str(exc)}
        if exc.run:
            payload["run"] = AIRecommendationRunSerializer(exc.run).data
        return Response(payload, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
def generate_for_farm(request, farm_id):
    farm = _farm(farm_id)
    device = None
    if request.data.get("device_id") is not None:
        device = get_object_or_404(FarmDevice, id=request.data["device_id"], farm=farm)
    return _generate(farm, device)


@api_view(["GET"])
def latest_recommendations(request, farm_id):
    farm = _farm(farm_id)
    run = AIRecommendationRun.objects.filter(farm=farm).first()
    if run is None:
        return Response({"detail": "No recommendation run exists for this farm."}, status=status.HTTP_404_NOT_FOUND)
    return Response(AIRecommendationRunSerializer(run, context={"request": request}).data)


@api_view(["GET"])
def recent_recommendations(request, farm_id):
    farm = _farm(farm_id)
    runs = AIRecommendationRun.objects.filter(farm=farm)[:3]
    return Response(AIRecommendationRunSerializer(runs, many=True, context={"request": request}).data)


@api_view(["POST"])
def recommend(request):
    farm_id = request.data.get("farm_id")
    if farm_id is None:
        return Response({"error": "farm_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    farm = _farm(farm_id)
    device = None
    if request.data.get("device_id") is not None:
        device = get_object_or_404(FarmDevice, id=request.data["device_id"], farm=farm)
    return _generate(farm, device)
