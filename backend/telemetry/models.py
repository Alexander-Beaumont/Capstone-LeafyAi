from django.db import models

# Create your models here.

class Farm(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)

class FarmDevice(models.Model):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE
    ) #cascade?
    name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=100,
                                   blank=True, null=True)

class FarmLevel(models.Model): #change many to many for plant batch
    device = models.ForeignKey(
        FarmDevice, 
        on_delete=models.CASCADE)
    level_number = models.IntegerField(
        choices=[(1, 'Top'), (2, 'Bottom')]
        )
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(level_number__in=[1, 2]),
                name='level_number_must_be_1_or_2'
            ),
            models.UniqueConstraint(
                fields=['device', 'level_number'],
                name='unique_level_per_device'
            )
    ]

# Growing Areas & slots

class GrowingArea(models.Model):
    farm_level = models.ForeignKey(FarmLevel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slot_count = models.IntegerField()

class Slot(models.Model):
    growing_area = models.ForeignKey(GrowingArea, on_delete=models.CASCADE)
    slot_number = models.IntegerField()
    row = models.IntegerField(
        blank=True,
        null=True
    )
    column = models.IntegerField(
        blank=True,
        null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['growing_area', 'slot_number'],
                name='unique_slot_per_growing_area'
            )
        ]

#Batch Management
class PlantBatch(models.Model):
    plant_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    growth_stage = models.CharField(
        max_length=50,
        choices=[
            ('seedling', 'Seedling'),
            ('early_growth', 'Early Growth'),
            ('mature', 'Mature'),
        ]
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('harvested', 'Harvested'),
            ('failed', 'Failed'),
        ]
    )

class BatchPlacement(models.Model): #
    plant_batch = models.ForeignKey(PlantBatch, on_delete=models.CASCADE)
    growing_area = models.ForeignKey(GrowingArea, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)

#camera & vision

class Camera(models.Model):
    farm_level = models.ForeignKey(FarmLevel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=100, blank=True, null=True)
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('RTSP', 'RTSP'),
            ('WEBCAM', 'Webcam'),
        ]
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    rtsp_port = models.IntegerField(blank=True, null=True)
    rtsp_path = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    webcam_index = models.IntegerField(blank=True, null=True)
    lighting_mode = models.CharField(
        max_length=20,
        choices=[
            ('NORMAL', 'Normal'),
            ('MAGENTA', 'Magenta'),
        ]
    )
    roi_points = models.JSONField(blank=True, null=True)  # Store ROI points as a list of dictionaries
    calibration_start_x = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True 
    )
    calibration_start_y = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True
    )
    calibration_end_x = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True
    )
    calibration_end_y = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True
    )
    calibration_length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    enabled = models.BooleanField(default=True)

class CameraSlotPosition(models.Model): #composite may need fixing
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    centre_x = models.DecimalField(
        max_digits=8, 
        decimal_places=6)
    centre_y = models.DecimalField(
        max_digits=8,
        decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['camera', 'slot'],
                name='unique_camera_slot_position'
            )
        ]

class CameraImage(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now=True)
    path = models.ImageField(
        upload_to="camera_images/"
    )
    


class Sensor(models.Model):
    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    sensor_type = models.CharField(max_length=50)
    unit = models.CharField(max_length=50)

class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    value = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

#Device-level Hardware

class NutrientTank(models.Model):
    device = models.OneToOneField(
        FarmDevice,
        on_delete=models.CASCADE)
    capacity_l = models.DecimalField(
        max_digits=6,
        decimal_places=1
    )
    current_level_l = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True
    )
    last_refill_date = models.DateTimeField(
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

class Doser(models.Model):
    device = models.ForeignKey(
        FarmDevice,
        on_delete=models.CASCADE)
    chemical_type = models.CharField(max_length=50)
    concentration = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True
    )
    flow_rate_ml_per_min = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

class SafeRange(models.Model):
    sensor_type = models.CharField(max_length=50)
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True
    )
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ]
    )
