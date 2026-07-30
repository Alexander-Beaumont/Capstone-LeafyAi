from django.db import models

# Create your models here.

class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class FarmLevel(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    level_number = models.PositiveIntegerField()

class plantBatch(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    plant_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    growth_stage = models.CharField(max_length=100)
    status = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.farm.name} - Level {self.level}"

class camera(models.Model):
    farm = models.ForeignKey(FarmLevel, on_delete=models.CASCADE)
    camera_id = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.farmLevel.farm.name} - Camera {self.camera_id}"

class cameraImage(models.Model):
    camera = models.ForeignKey(camera, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='camera_images/')

    def __str__(self):
        return f"{self.camera.farmLevel.farm.name} - Camera {self.camera.camera_id} - {self.timestamp}"

