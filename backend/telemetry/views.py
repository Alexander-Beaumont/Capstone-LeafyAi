from rest_framework import status, viewsets
from rest_framework.response import Response
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


class PlantBatchViewSet(viewsets.ModelViewSet):
    queryset = PlantBatch.objects.all()
    serializer_class = PlantBatchSerializer


class BatchPlacementViewSet(viewsets.ModelViewSet):
    queryset = BatchPlacement.objects.all()
    serializer_class = BatchPlacementSerializer


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.select_related("farm_level").all().order_by("id")
    serializer_class = CameraSerializer

    def get_queryset(self):
        queryset = self.queryset.all()
        if self.action == "list":
            queryset = queryset.filter(is_archived=False)
        return queryset

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Hard delete is disabled. Archive the camera with PATCH is_archived=true."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class CameraImageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CameraImage.objects.select_related("camera").all().order_by("-captured_at", "-id")
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
