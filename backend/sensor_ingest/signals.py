from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from sensor_ingest.models import SensorIngestConfiguration
from telemetry.models import FarmDevice


@receiver(post_save, sender=FarmDevice)
def ensure_ingest_configuration(sender, instance, created, **kwargs):
    if not created:
        return
    environment_device = str(settings.SENSOR_INGEST_DEVICE_SLUG or "").strip()
    uses_environment = bool(environment_device and instance.slug == environment_device)
    SensorIngestConfiguration.objects.get_or_create(
        device=instance,
        defaults={
            "enabled": uses_environment and bool(settings.LEAFY_WATER_QUALITY_URL) and bool(settings.LEAFY_AMBIENT_SENSOR_URL),
            "water_quality_url": str(settings.LEAFY_WATER_QUALITY_URL or "").strip() if uses_environment else "",
            "ambient_sensor_url": str(settings.LEAFY_AMBIENT_SENSOR_URL or "").strip() if uses_environment else "",
            "poll_interval_seconds": int(settings.SENSOR_INGEST_POLL_SECONDS),
            "sensor_stale_threshold_seconds": int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS),
        },
    )
