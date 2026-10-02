from __future__ import annotations

from telemetry.models import Farm

from .models import PowerboardConfiguration


def powerboards_for_farm(farm_id: int) -> dict[str, dict[str, str]]:
    """Return the two physical strip addresses configured for one farm.

    Farm-scoped callers deliberately do not fall back to another farm's/global
    addresses. A missing value therefore surfaces as NOT_CONFIGURED from the
    existing Kasa controller instead of contacting the wrong strip.
    """
    if not Farm.objects.filter(pk=farm_id).exists():
        raise Farm.DoesNotExist

    config = PowerboardConfiguration.objects.filter(farm_id=farm_id).first()
    return {
        "board_1": {"ip": str(config.powerboard_1_ip or "") if config else ""},
        "board_2": {"ip": str(config.powerboard_2_ip or "") if config else ""},
    }
