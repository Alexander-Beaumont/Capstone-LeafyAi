"""Small idempotent bootstrap for Leafy AI's physical farm structure.

The frontend expects FarmLevel rows to exist before a Camera is created.  This
module creates only the minimum shared farm metadata needed by the existing
APIs: one Farm, one FarmDevice/grow rack, and levels 1 and 2.

It deliberately does *not* create Cameras, GrowingAreas, batches, sensors, or
other user/runtime data.
"""

from __future__ import annotations

import os

from telemetry.models import Farm, FarmDevice, FarmLevel


def _env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value or default


def ensure_default_farm_structure() -> dict[str, object]:
    """Ensure the minimum farm/rack/level structure exists.

    The operation is idempotent and intentionally conservative with an
    existing database:

    * If a Farm with the configured name exists, use it.
    * Otherwise, if any Farm already exists, use the first one instead of
      creating a competing farm hierarchy.
    * Apply the same rule to FarmDevice inside that Farm.
    * Ensure FarmLevel 1 and FarmLevel 2 exist for the selected device.

    Returns a small summary that is useful in tests and startup logging.
    """

    farm_name = _env("LEAFY_FARM_NAME", "LeafyAI Farm")
    farm_location = _env("LEAFY_FARM_LOCATION", "Melbourne")
    rack_name = _env("LEAFY_RACK_NAME", "LeafyAI Grow Rack")

    created: list[str] = []

    farm = Farm.objects.filter(name=farm_name).order_by("id").first()
    if farm is None:
        farm = Farm.objects.order_by("id").first()
    if farm is None:
        farm = Farm.objects.create(name=farm_name, location=farm_location)
        created.append("farm")
    elif not farm.location and farm_location:
        # Fill missing metadata without overwriting an existing location.
        farm.location = farm_location
        farm.save(update_fields=["location"])

    device = (
        FarmDevice.objects.filter(farm=farm, name=rack_name)
        .order_by("id")
        .first()
    )
    if device is None:
        device = FarmDevice.objects.filter(farm=farm).order_by("id").first()
    if device is None:
        device = FarmDevice.objects.create(
            farm=farm,
            name=rack_name,
            device_type="grow_rack",
        )
        created.append("farm_device")

    levels: list[FarmLevel] = []
    for level_number in (1, 2):
        level, was_created = FarmLevel.objects.get_or_create(
            device=device,
            level_number=level_number,
        )
        levels.append(level)
        if was_created:
            created.append(f"farm_level_{level_number}")

    return {
        "farm_id": farm.id,
        "device_id": device.id,
        "level_ids": [level.id for level in levels],
        "created": created,
    }
