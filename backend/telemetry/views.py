from rest_framework import viewsets
from telemetry.models import *
from telemetry.serializers import *


# Create your views here.
class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer

class FarmLevelViewSet(viewsets.ModelViewSet):
    queryset = FarmLevel.objects.all()
    serializer_class = FarmLevelSerializer

class PlantBatchViewSet(viewsets.ModelViewSet):
    queryset = PlantBatch.objects.all()
    serializer_class = PlantBatchSerializer

class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

class CameraImageViewSet(viewsets.ModelViewSet):
    queryset = CameraImage.objects.all()
    serializer_class = CameraImageSerializer

class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer

class SensorReadingViewSet(viewsets.ModelViewSet):
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer
