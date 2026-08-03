from django.db import models
from telemetry.models import CameraImage

class ImageAnalysis(models.Model):
    image = models.OneToOneField(CameraImage, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_canopy_coverage = models.FloatField()
    visible_plant_count = models.IntegerField()
    measurement_valid = models.BooleanField()
    processing_time_ms = models.IntegerField()

class PlantVisionMeasurement(models.Model):
    analysis = models.ForeignKey(ImageAnalysis, on_delete=models.CASCADE)
    slot_id = models.IntegerField()
    canopy_coverage = models.FloatField()
    width_px = models.FloatField()
    height_px = models.FloatField()
    width_cm = models.FloatField()
    height_cm = models.FloatField()
    green_percentage = models.FloatField()
    yellow_percentage = models.FloatField()
    crowding_percentage = models.FloatField()
    growth_change = models.FloatField()
    visible = models.BooleanField()
    measurement_valid = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)