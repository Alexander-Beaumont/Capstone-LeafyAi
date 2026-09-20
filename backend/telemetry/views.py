from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

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


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def official_image(request, camera_id):
    """Persist one raw official camera image without running CV analysis."""
    camera = get_object_or_404(Camera, id=camera_id)
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"detail": "image is required"}, status=status.HTTP_400_BAD_REQUEST)
    captured_value = request.data.get("captured_at")
    captured_at = parse_datetime(str(captured_value)) if captured_value else timezone.now()
    if captured_at is None:
        return Response(
            {"detail": "captured_at must be a valid ISO 8601 datetime"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    image = CameraImage.objects.create(camera=camera, captured_at=captured_at, path=image_file)
    payload = CameraImageSerializer(image, context={"request": request}).data
    payload.update({"image_id": image.id, "camera_id": camera.id, "image_url": payload.get("path")})
    return Response(payload, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def latest_image(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    image = CameraImage.objects.filter(camera=camera).order_by("-captured_at", "-id").first()
    if image is None:
        return Response({"detail": "No image found for this camera."}, status=status.HTTP_404_NOT_FOUND)
    payload = CameraImageSerializer(image, context={"request": request}).data
    payload.update({"image_id": image.id, "camera_id": camera.id, "image_url": payload.get("path")})
    return Response(payload)
