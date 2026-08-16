from rest_framework import viewsets

from computer_vision.models import (
    ImageAnalysis,
    PlantVisionMeasurement,
)

from computer_vision.serializers import (
    ImageAnalysisSerializer,
    PlantVisionMeasurementSerializer,
)


class ImageAnalysisViewSet(viewsets.ModelViewSet):
    queryset = ImageAnalysis.objects.all()
    serializer_class = ImageAnalysisSerializer


class PlantVisionMeasurementViewSet(viewsets.ModelViewSet):
    queryset = PlantVisionMeasurement.objects.all()
    serializer_class = PlantVisionMeasurementSerializer