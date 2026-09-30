from sensor_ingest.services.configuration import ensure_sensor_definitions
from telemetry.models import FarmDevice, FarmLevel


def provision_farm(farm):
    """Create the editable controller layout required by a new farm."""

    device = FarmDevice.objects.create(
        farm=farm,
        name="Controller",
        device_type="controller",
    )
    ensure_sensor_definitions(device)
    FarmLevel.objects.bulk_create(
        [
            FarmLevel(device=device, level_number=1),
            FarmLevel(device=device, level_number=2),
        ]
    )
    return device
