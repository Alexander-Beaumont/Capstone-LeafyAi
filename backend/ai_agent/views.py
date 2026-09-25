from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers
from core.pagination import OperatorLimitOffsetPagination

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


def _filter_datetime(request, name):
    aliases = {
        "start": ("start", "start_at", "date_from"),
        "end": ("end", "end_at", "date_to"),
    }
    value = next(
        (request.query_params.get(key) for key in aliases.get(name, (name,)) if request.query_params.get(key)),
        None,
    )
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise serializers.ValidationError({name: "Use an ISO 8601 date-time."})
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


@api_view(["GET"])
def recommendation_history(request, farm_id):
    farm = _farm(farm_id)
    queryset = AIRecommendationRun.objects.filter(farm=farm).prefetch_related(
        "source_images__camera", "source_readings__sensor", "recommendations__actions"
    ).order_by("-created_at", "-id")
    filters = {
        "status": (request.query_params.get("status"), dict(AIRecommendationRun.STATUS_CHOICES)),
        "trigger": (request.query_params.get("trigger"), dict(AIRecommendationRun.TRIGGER_CHOICES)),
        "input_mode": (request.query_params.get("input_mode"), dict(AIRecommendationRun.INPUT_MODE_CHOICES)),
    }
    for field, (value, choices) in filters.items():
        if value:
            if value not in choices:
                raise serializers.ValidationError({field: f"Unsupported {field}."})
            queryset = queryset.filter(**{field: value})
    start = _filter_datetime(request, "start")
    end = _filter_datetime(request, "end")
    if start:
        queryset = queryset.filter(created_at__gte=start)
    if end:
        queryset = queryset.filter(created_at__lte=end)
    paginator = OperatorLimitOffsetPagination()
    page = paginator.paginate_queryset(queryset, request)
    data = AIRecommendationRunSerializer(page, many=True, context={"request": request}).data
    return paginator.get_paginated_response(data)


@api_view(["GET"])
def recommendation_detail(request, farm_id, run_id):
    run = get_object_or_404(
        AIRecommendationRun.objects.prefetch_related(
            "source_images__camera", "source_readings__sensor",
            "recommendations__actions", "recommendations__safetycheck",
        ),
        id=run_id,
        farm_id=farm_id,
    )
    return Response(AIRecommendationRunSerializer(run, context={"request": request}).data)


@api_view(["POST"])
def recommend(request):
    if request.data.get("farm_id") is None: return Response({"error": "farm_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    farm = _farm(request.data["farm_id"])
    device = get_object_or_404(FarmDevice, id=request.data["device_id"], farm=farm) if request.data.get("device_id") is not None else None
    return _generate(farm, device)
