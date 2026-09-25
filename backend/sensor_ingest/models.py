from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from telemetry.models import FarmDevice


class SensorIngestConfiguration(models.Model):
    """Runtime-editable HTTP ingestion settings for one physical controller."""

    device = models.OneToOneField(
        FarmDevice,
        on_delete=models.CASCADE,
        related_name="sensor_ingest_configuration",
    )
    enabled = models.BooleanField(default=True)
    water_quality_url = models.URLField(max_length=500, blank=True, default="")
    ambient_sensor_url = models.URLField(max_length=500, blank=True, default="")
    poll_interval_seconds = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(86400)],
    )
    sensor_stale_threshold_seconds = models.PositiveIntegerField(
        default=120,
        validators=[MinValueValidator(1), MaxValueValidator(604800)],
    )
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    consecutive_failures = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["device_id"]
