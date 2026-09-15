from __future__ import annotations
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .bridge import get_powerboard_bridge

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def devices(_request):
    try:
        return Response(get_powerboard_bridge().get_all_device_statuses())
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def device_state(request, device_id: int):
    requested = str(request.data.get("state", "")).upper().strip()
    if requested not in {"ON", "OFF"}:
        return Response({"detail": "state must be ON or OFF"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(get_powerboard_bridge().set_device_state(device_id, requested))
    except (ValueError, KeyError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def magenta_state(request):
    bridge = get_powerboard_bridge()
    try:
        if request.method == "GET":
            return Response(bridge.get_magenta_state())
        requested = str(request.data.get("state", "")).upper().strip()
        if requested not in {"ON", "OFF"}:
            return Response({"detail": "state must be ON or OFF"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(bridge.set_magenta_state(requested))
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
