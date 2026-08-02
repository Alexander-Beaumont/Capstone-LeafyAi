from django.db import models
from telemetry.models import CameraImage

class ImageAnalysis(models.Model):
    image = models.OneToOneField(CameraImage, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_canopy_coverage = models.FloatField()
    visible_plant_count = models.IntegerField()
    measurement_valid = models.BooleanField()
    processing_time_ms = models.IntegerField()