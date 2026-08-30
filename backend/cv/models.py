from django.db import models
from telemetry.models import CameraImage, Slot

class ImageAnalysis(models.Model):
    image = models.OneToOneField(
        CameraImage,
        on_delete=models.CASCADE,
        related_name="analysis"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_canopy_coverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        #blank=True,
        null=True
    )
    growth_change = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        #blank=True,
        null=True
    )
    crowding_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        #blank=True,
        null=True
    )
    green_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        #blank=True,
        null=True
    )
    yellow_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        #blank=True,
        null=True
    )
    measurement_valid = models.BooleanField(default=True)
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
    )
    vlm_ready = models.BooleanField(default=False)
    quality_status = models.CharField(
        max_length=16,
        default="UNKOWN"
    )
    quality_flags = models.JSONField(default=list)
    quality_message = models.TextField(default="")
