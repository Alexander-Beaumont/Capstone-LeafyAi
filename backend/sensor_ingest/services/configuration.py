from django.conf import settings

from sensor_ingest.models import SensorIngestConfiguration
from sensor_ingest.services.mapper import SENSOR_DEFINITIONS
from telemetry.models import FarmDevice, Sensor


def ensure_sensor_definitions(device, *, force_timing=False):
    """Create the standard physical sensor definitions for one controller."""

    expected = int(settings.SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS)
    stale = int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS)
    created_count = 0
    updated_count = 0

    # Sensor slugs are the stable contract shared by ingestion, farm_state and AI.
    # Existing rows are updated only where the canonical definition requires it.
    for definition in SENSOR_DEFINITIONS:
        defaults = {
            "sensor_type": definition.sensor_type,
            "unit": definition.unit,
            "enabled": True,
            "expected_interval_seconds": expected,
            "stale_after_seconds": stale,
        }
        sensor, created = Sensor.objects.get_or_create(
            device=device,
            slug=definition.slug,
            defaults=defaults,
        )
        if created:
            created_count += 1
            continue

        changed_fields = []
        if sensor.sensor_type != definition.sensor_type:
            sensor.sensor_type = definition.sensor_type
            changed_fields.append("sensor_type")
        if sensor.unit != definition.unit:
            sensor.unit = definition.unit
            changed_fields.append("unit")
        if force_timing:
            if sensor.expected_interval_seconds != expected:
                sensor.expected_interval_seconds = expected
                changed_fields.append("expected_interval_seconds")
            if sensor.stale_after_seconds != stale:
                sensor.stale_after_seconds = stale
                changed_fields.append("stale_after_seconds")
        if changed_fields:
            sensor.save(update_fields=changed_fields)
            updated_count += 1

    return created_count, updated_count


def propagate_sensor_timing(configuration):
    Sensor.objects.filter(device=configuration.device).update(
        expected_interval_seconds=configuration.poll_interval_seconds,
        stale_after_seconds=configuration.sensor_stale_threshold_seconds,
    )


def bootstrap_environment_configuration(device=None):
    slug = str(settings.SENSOR_INGEST_DEVICE_SLUG or "").strip()
    if device is None:
        if not slug:
            return None, False
        device = FarmDevice.objects.filter(slug=slug).first()
    if device is None:
        return None, False
    # Environment values bootstrap the first configuration only; after creation,
    # the database row is the runtime-editable source used by the operator API.
    configuration, created = SensorIngestConfiguration.objects.get_or_create(
        device=device,
        defaults={
            "enabled": True,
            "water_quality_url": str(settings.LEAFY_WATER_QUALITY_URL or "").strip(),
            "ambient_sensor_url": str(settings.LEAFY_AMBIENT_SENSOR_URL or "").strip(),
            "poll_interval_seconds": int(settings.SENSOR_INGEST_POLL_SECONDS),
            "sensor_stale_threshold_seconds": int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS),
        },
    )
    if created:
        propagate_sensor_timing(configuration)
    return configuration, created
