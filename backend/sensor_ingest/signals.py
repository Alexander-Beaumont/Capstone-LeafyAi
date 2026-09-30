from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from sensor_ingest.models import SensorIngestConfiguration
from sensor_ingest.services.mapper import SENSOR_DEFINITIONS
from telemetry.models import FarmDevice, Sensor


def ensure_required_sensors(device):
    """
    Ensure every LeafyAI controller has the seven physical sensor definitions.
    """

    # Only controller-type FarmDevices own the physical farm sensors.
    if device.device_type not in {
        "controller",
        "hydroponic_controller",
    }:
        return

    expected = int(settings.SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS)
    stale = int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS)

    for definition in SENSOR_DEFINITIONS:
        sensor, created = Sensor.objects.get_or_create(
            device=device,
            slug=definition.slug,
            defaults={
                "sensor_type": definition.sensor_type,
                "unit": definition.unit,
                "enabled": True,
                "expected_interval_seconds": expected,
                "stale_after_seconds": stale,
            },
        )

        if created:
            continue

        changed_fields = []

        if sensor.sensor_type != definition.sensor_type:
            sensor.sensor_type = definition.sensor_type
            changed_fields.append("sensor_type")

        if sensor.unit != definition.unit:
            sensor.unit = definition.unit
            changed_fields.append("unit")

        # A required physical sensor must be enabled.
        if not sensor.enabled:
            sensor.enabled = True
            changed_fields.append("enabled")

        if changed_fields:
            sensor.save(update_fields=changed_fields)


@receiver(post_save, sender=FarmDevice)
def ensure_ingest_configuration(sender, instance, created, **kwargs):
    if not created:
        return

    environment_device = str(
        settings.SENSOR_INGEST_DEVICE_SLUG or ""
    ).strip()

    uses_environment = bool(
        environment_device
        and instance.slug == environment_device
    )

    SensorIngestConfiguration.objects.get_or_create(
        device=instance,
        defaults={
            "enabled": (
                uses_environment
                and bool(settings.LEAFY_WATER_QUALITY_URL)
                and bool(settings.LEAFY_AMBIENT_SENSOR_URL)
            ),
            "water_quality_url": (
                str(settings.LEAFY_WATER_QUALITY_URL or "").strip()
                if uses_environment
                else ""
            ),
            "ambient_sensor_url": (
                str(settings.LEAFY_AMBIENT_SENSOR_URL or "").strip()
                if uses_environment
                else ""
            ),
            "poll_interval_seconds": int(
                settings.SENSOR_INGEST_POLL_SECONDS
            ),
            "sensor_stale_threshold_seconds": int(
                settings.SENSOR_INGEST_SENSOR_STALE_SECONDS
            ),
        },
    )

    # Important:
    # FarmDevice creation also creates its seven required Sensor rows.
    ensure_required_sensors(instance)
