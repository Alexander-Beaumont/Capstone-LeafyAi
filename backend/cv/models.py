from django.db import models
from telemetry.models import CameraImage, Slot

class ImageAnalysis(models.Model):
    image = models.ForeignKey(
        CameraImage,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_canopy_coverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    visible_plant_count = models.IntegerField(
        blank=True,
        null=True)
    measurement_valid = models.BooleanField(default=True)
    processing_time_ms = models.IntegerField(
        blank=True,
        null=True
    )

class PlantVisionMeasurement(models.Model):
    image_analysis = models.ForeignKey(
        ImageAnalysis,
        on_delete=models.CASCADE)
    slot = models.ForeignKey(
        Slot,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    canopy_coverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    width_px = models.IntegerField(
        blank=True,
        null=True
    )
    height_px = models.IntegerField(
        blank=True,
        null=True
    )
    width_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True
    )
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True
    )
    green_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    yellow_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    crowding_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    growth_stage = models.CharField(
        max_length=20,
        choices=[
            ('seedling', 'Seedling'),
            ('early_growth', 'Early Growth'),
            ('mature', 'Mature'),
        ],
        blank=True,
        null=True
    )
    growth_change = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    visible = models.BooleanField(default=True)
    measurement_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["image_analysis", "slot"],
                name="unique_cv_measurement_per_slot_analysis"
            )
        ]