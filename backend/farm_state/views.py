from django.shortcuts import render

from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response

from telemetry.models import Farm
from farm_state.services import build_farm_state

@api_view(["GET"])
def farm_state(request, farm_id):
    """GET /api/farm-state/<farm_id>/"""
    farm = get_object_or_404(Farm, id=farm_id)
    # The view only resolves the farm and calls the service.
    # No aggregation logic lives here.
    return Response(build_farm_state(farm))