from django.db import models

# Create your models here.

class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class FarmLevel(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    plantBatch = models.ForeignKey('PlantBatch', on_delete=models.CASCADE)
    sensor = models.ForeignKey('Sensor', on_delete=models.CASCADE)
    level_number = models.PositiveIntegerField()

class PlantBatch(models.Model):
    plant_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    growth_stage = models.CharField(max_length=100)
    status = models.CharField(max_length=100)

    def __str__(self):
        return f" Plant type: {self.plant_type} \n planting_date: {self.planting_date} \n growth_stage: {self.growth_stage} \n status {self.status}"

class Camera(models.Model):
    farm = models.ForeignKey(FarmLevel, on_delete=models.CASCADE)
    camera_id = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.farm.name} - Camera {self.camera_id}"

class cameraImage(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    # May need to install Pillow package for ImageField
    # image = models.ImageField(upload_to='camera_images/')

    def __str__(self):
        return f"{self.camera.farmLevel.farm.name} - Camera {self.camera.camera_id} - {self.timestamp}"

class Sensor(models.Model):
    sensor_type = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.sensor_type} ({self.unit})"

class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    timestamp= models.DateTimeField(auto_now_add=True)
    value = models.FloatField()

    def __str__(self):
        return f"{self.sensor.sensor_type} - {self.value} {self.sensor.unit} at {self.timestamp}"