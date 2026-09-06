from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from telemetry.models import Farm, FarmDevice

from ai_agent.models import *
from ai_agent.serializers import *
from ai_agent.services import generate_recommendation, NoDeviceError


class AIDecisionViewSet(viewsets.ModelViewSet):
    queryset = AIDecision.objects.all()
    serializer_class = AIDecisionSerializer


class FarmActionViewSet(viewsets.ModelViewSet):
    queryset = FarmAction.objects.all()
    serializer_class = FarmActionSerializer

class HumanApprovalViewSet(viewsets.ModelViewSet):
    queryset = HumanApproval.objects.all()
    serializer_class = HumanApprovalSerializer


class SafetyCheckViewSet(viewsets.ModelViewSet):
    queryset = SafetyCheck.objects.all()
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

    return Response(result, status=status.HTTP_201_CREATED)
