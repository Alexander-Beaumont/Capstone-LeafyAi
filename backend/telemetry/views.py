from rest_framework import viewsets
from telemetry.models import *
from telemetry.serializers import *


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer


class FarmDeviceViewSet(viewsets.ModelViewSet):
    queryset = FarmDevice.objects.all()
    serializer_class = FarmDeviceSerializer


class FarmLevelViewSet(viewsets.ModelViewSet):
    queryset = FarmLevel.objects.all()
    serializer_class = FarmLevelSerializer


class GrowingAreaViewSet(viewsets.ModelViewSet):
    queryset = GrowingArea.objects.all()
    serializer_class = GrowingAreaSerializer


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all()
    serializer_class = SlotSerializer


class PlantBatchViewSet(viewsets.ModelViewSet):
    queryset = PlantBatch.objects.all()
    serializer_class = PlantBatchSerializer


class BatchPlacementViewSet(viewsets.ModelViewSet):
    queryset = BatchPlacement.objects.all()
    serializer_class = BatchPlacementSerializer


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer


class CameraSlotPositionViewSet(viewsets.ModelViewSet):
    queryset = CameraSlotPosition.objects.all()
    serializer_class = CameraSlotPositionSerializer

#slot position is filterable by camera. so Get /api/camera-slot-postions/?camera=1
#should only return slots associated with camera 1
    def get_queryset(self):
        queryset = CameraSlotPosition.objects.all()

        camera_id = self.request.query_params.get("camera")

        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)

        return queryset


class CameraImageViewSet(viewsets.ModelViewSet):
    queryset = CameraImage.objects.all()
    serializer_class = CameraImageSerializer


class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class SensorReadingViewSet(viewsets.ModelViewSet):
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer


class NutrientTankViewSet(viewsets.ModelViewSet):
    queryset = NutrientTank.objects.all()
    serializer_class = NutrientTankSerializer


class DoserViewSet(viewsets.ModelViewSet):
    queryset = Doser.objects.all()
    serializer_class = DoserSerializer


class SafeRangeViewSet(viewsets.ModelViewSet):
    queryset = SafeRange.objects.all()
    serializer_class = SafeRangeSerializer