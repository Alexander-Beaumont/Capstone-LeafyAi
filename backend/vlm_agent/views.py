from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from telemetry.models import Farm, FarmDevice
from vlm_agent.models import VLMDecision, VLMFarmAction, VLMHumanApproval, VLMSafetyCheck
from vlm_agent.serializers import (
    VLMDecisionSerializer,
    VLMFarmActionSerializer,
    VLMHumanApprovalSerializer,
    VLMSafetyCheckSerializer,
)
from vlm_agent.services import NoDeviceError, generate_recommendation


class VLMDecisionViewSet(viewsets.ModelViewSet):
    queryset = VLMDecision.objects.all()
    serializer_class = VLMDecisionSerializer


class VLMFarmActionViewSet(viewsets.ModelViewSet):
    queryset = VLMFarmAction.objects.all()
    serializer_class = VLMFarmActionSerializer


class VLMHumanApprovalViewSet(viewsets.ModelViewSet):
    queryset = VLMHumanApproval.objects.all()
    serializer_class = VLMHumanApprovalSerializer


class VLMSafetyCheckViewSet(viewsets.ModelViewSet):
    queryset = VLMSafetyCheck.objects.all()
    serializer_class = VLMSafetyCheckSerializer


@api_view(["POST"])
def recommend(request):
    farm_id = request.data.get("farm_id")
    if farm_id is None:
        return Response({"error": "farm_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    farm = get_object_or_404(Farm, id=farm_id)
    device = None
    device_id = request.data.get("device_id")
    if device_id is not None:
        device = get_object_or_404(FarmDevice, id=device_id, farm=farm)

    try:
        result = generate_recommendation(farm, device=device)
    except NoDeviceError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_201_CREATED)
