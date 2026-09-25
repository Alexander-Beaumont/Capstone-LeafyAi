from django.conf import settings

from sensor_ingest.models import SensorIngestConfiguration
from telemetry.models import FarmDevice, Sensor


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
