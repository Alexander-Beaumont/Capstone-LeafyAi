from django.db import models
from rest_framework import serializers
from telemetry.models import *

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ['id', 'name', 'location']


class FarmLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmLevel
        fields = ["id", "farm", "plantBatch", "sensor", "level_number"]


class PlantBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantBatch
        fields = ['id', 'plant_type', 'planting_date', 'growth_stage', 'status']


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'farm', 'camera_id']


class CameraImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraImage
        fields = ['id', 'camera', 'timestamp']  # , 'image']  # Uncomment 'image' if using ImageField


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id', 'sensor_type', 'unit']


class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = ['id', 'sensor', 'timestamp', 'value']

    