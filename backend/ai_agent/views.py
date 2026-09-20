from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from telemetry.models import Farm, FarmDevice

from ai_agent.models import *
from ai_agent.serializers import *
from ai_agent.services import (
    NoDeviceError,
    RecommendationGenerationError,
    generate_recommendation,
)


class AIDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIDecision.objects.select_related("safetycheck").order_by("-created_at", "-id")
    serializer_class = AIDecisionSerializer


class FarmActionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FarmAction.objects.order_by("-id")
    serializer_class = FarmActionSerializer

class SafetyCheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SafetyCheck.objects.order_by("-checked_at", "-id")
    serializer_class = SafetyCheckSerializer


@api_view(["POST"])
def recommend(request):
    """Generate a recommendation for a farm.

    POST /api/ai-agent/recommend/
    Body: {"farm_id": 1, "device_id": 1 (optional)}
    """
    farm_id = request.data.get("farm_id")
    if farm_id is None:
        return Response(
            {"error": "farm_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    farm = get_object_or_404(Farm, id=farm_id)

    device = None
    device_id = request.data.get("device_id")
    if device_id is not None:
        device = get_object_or_404(FarmDevice, id=device_id, farm=farm)

    try:
        result = generate_recommendation(farm, device=device)
    except NoDeviceError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except RecommendationGenerationError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response(result, status=status.HTTP_201_CREATED)
