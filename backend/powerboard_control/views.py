from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from telemetry.models import Farm

from .bridge import get_powerboard_bridge
from .models import PowerboardConfiguration
from .serializers import PowerboardConfigurationSerializer
from .runtime_config import powerboards_for_farm


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def devices(request):
    try:
        farm_id = request.query_params.get("farm_id")
        powerboards = powerboards_for_farm(int(farm_id)) if farm_id else None
        return Response(get_powerboard_bridge(powerboards).get_all_device_statuses())
    except Farm.DoesNotExist:
        return Response(
            {"detail": "Farm not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except (TypeError, ValueError):
        return Response(
            {"detail": "farm_id must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# State changes are always confirmed through the shared Kasa bridge before the
# API returns success to the frontend.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def device_state(request, device_id: int):
    requested = str(request.data.get("state", "")).upper().strip()
    if requested not in {"ON", "OFF"}:
        return Response(
            {"detail": "state must be ON or OFF"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        farm_id = request.data.get("farm_id") or request.query_params.get("farm_id")
        powerboards = powerboards_for_farm(int(farm_id)) if farm_id else None
        return Response(
            get_powerboard_bridge(powerboards).set_device_state(device_id, requested)
        )
    except Farm.DoesNotExist:
        return Response(
            {"detail": "Farm not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except (ValueError, KeyError) as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def farm_powerboard_config(request, farm_id: int):
    """Read or update the two physical Powerboard IPs assigned to a farm.

    This intentionally does not change the existing ``/api/devices/`` or
    ``/api/devices/<id>/state/`` contracts. The fixed logical outlet mapping
    remains in ``powerboard_control.config.DEVICES``.
    """
    try:
        farm = Farm.objects.get(pk=farm_id)
    except Farm.DoesNotExist:
        return Response(
            {"detail": "Farm not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    configuration, _ = PowerboardConfiguration.objects.get_or_create(farm=farm)

    if request.method == "GET":
        return Response(PowerboardConfigurationSerializer(configuration).data)

    serializer = PowerboardConfigurationSerializer(
        configuration,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
