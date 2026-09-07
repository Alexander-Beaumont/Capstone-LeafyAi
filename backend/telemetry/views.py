from rest_framework import viewsets

from telemetry.models import (
    ActuatorStateObservation,
    BatchPlacement,
    Camera,
    CameraImage,
    Doser,
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    NutrientTank,
    PlantBatch,
    SafeRange,
    Sensor,
    SensorReading,
    SetpointObservation,
)
from telemetry.serializers import (
    ActuatorStateObservationSerializer,
    BatchPlacementSerializer,
    CameraImageSerializer,
    CameraSerializer,
    DoserSerializer,
    FarmDeviceSerializer,
    FarmLevelSerializer,
    FarmSerializer,
    GrowingAreaSerializer,
    NutrientTankSerializer,
    PlantBatchSerializer,
    SafeRangeSerializer,
    SensorReadingSerializer,
    SensorSerializer,
    SetpointObservationSerializer,
)


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
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer


class CameraImageViewSet(viewsets.ModelViewSet):
    queryset = CameraImage.objects.all()
    serializer_class = CameraImageSerializer


class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class SensorReadingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SensorReading.objects.select_related("sensor").order_by(
        "-measured_at", "-id"
    )
    serializer_class = SensorReadingSerializer


class ActuatorStateObservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActuatorStateObservation.objects.select_related("device").order_by(
        "-measured_at", "-id"
    )
    serializer_class = ActuatorStateObservationSerializer


class SetpointObservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SetpointObservation.objects.select_related("device").order_by(
        "-measured_at", "-id"
    )
    serializer_class = SetpointObservationSerializer


class NutrientTankViewSet(viewsets.ModelViewSet):
    queryset = NutrientTank.objects.all()
    serializer_class = NutrientTankSerializer


class DoserViewSet(viewsets.ModelViewSet):
    queryset = Doser.objects.all()
    serializer_class = DoserSerializer


class SafeRangeViewSet(viewsets.ModelViewSet):
    queryset = SafeRange.objects.all()
    serializer_class = SafeRangeSerializer
