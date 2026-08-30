from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
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
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="official-image",
        parser_classes=[
            MultiPartParser,
            FormParser
        ]
    )
    def official_image(self, request, pk=None):

        # Camera is taken from the URL:
        # /api/cameras/{id}/official-image/
        camera = self.get_object()

        # Validate multipart input
        serializer = OfficialImageUploadSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        uploaded_image = serializer.validated_data[
            "image"
        ]

        captured_at = serializer.validated_data[
            "captured_at"
        ]

        # Create exactly one official CameraImage
        camera_image = CameraImage.objects.create(
            camera=camera,
            captured_at=captured_at,
            path=uploaded_image
        )

        return Response(
            {
                "image_id": camera_image.id,
                "camera_id": camera.id,
                "captured_at": camera_image.captured_at,
                "image_url": camera_image.path.url,
            },
            status=status.HTTP_201_CREATED
        )

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