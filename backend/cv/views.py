from rest_framework import viewsets, status

from cv.models import (
    ImageAnalysis,
    PlantVisionMeasurement,
)

from cv.serializers import (
    ImageAnalysisSerializer,
    PlantVisionMeasurementSerializer,
)
#unsure
import json
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from telemetry.models import Camera, CameraImage, Slot


class ImageAnalysisViewSet(viewsets.ModelViewSet):
    queryset = ImageAnalysis.objects.all()
    serializer_class = ImageAnalysisSerializer


class PlantVisionMeasurementViewSet(viewsets.ModelViewSet):
    queryset = PlantVisionMeasurement.objects.all()
    serializer_class = PlantVisionMeasurementSerializer



#The code below is with Ai. i need to test it
@api_view(['POST'])
@transaction.atomic
def ingest_cv_result(request):

    # LeafyCV can send either JSON or multipart form data.
    if 'metadata' in request.data:
        try:
            data = json.loads(request.data['metadata'])
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid metadata JSON"},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        data = request.data

    # -----------------------------
    # 1. Validate camera
    # -----------------------------

    camera_id = data.get('camera_id')

    if not camera_id:
        return Response(
            {"error": "camera_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    # -----------------------------
    # 2. Validate analysis data
    # -----------------------------

    analysis_data = data.get('analysis')

    if not analysis_data:
        return Response(
            {"error": "analysis is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # 3. Create CameraImage record
    # -----------------------------

    camera_image = CameraImage.objects.create(
        camera=camera,
        path=""
    )

    # -----------------------------
    # 4. Create ImageAnalysis
    # -----------------------------

    analysis = ImageAnalysis.objects.create(
        image=camera_image,

        total_canopy_coverage=
            analysis_data.get('total_canopy_coverage'),

        visible_plant_count=
            analysis_data.get('visible_plant_count'),

        measurement_valid=
            analysis_data.get('measurement_valid', True),

        processing_time_ms=
            analysis_data.get('processing_time_ms'),
    )

    # -----------------------------
    # 5. Create measurements
    # -----------------------------

    measurements_created = 0

    for plant in data.get('plants', []):

        slot_id = plant.get('slot_id')

        if not slot_id:
            continue

        slot = get_object_or_404(
            Slot,
            id=slot_id
        )

        PlantVisionMeasurement.objects.create(
            image_analysis=analysis,
            slot=slot,

            canopy_coverage=
                plant.get('canopy_coverage'),

            width_px=
                plant.get('width_px'),

            height_px=
                plant.get('height_px'),

            width_cm=
                plant.get('width_cm'),

            height_cm=
                plant.get('height_cm'),

            green_percentage=
                plant.get('green_percentage'),

            yellow_percentage=
                plant.get('yellow_percentage'),

            crowding_percentage=
                plant.get('crowding_percentage'),

            growth_change=
                plant.get('growth_change'),

            visible=
                plant.get('visible', True),

            measurement_valid=
                plant.get('measurement_valid', True),
        )

        measurements_created += 1

    # -----------------------------
    # 6. Return success
    # -----------------------------

    return Response(
        {
            "message": "LeafyCV result stored successfully",
            "camera_image_id": camera_image.id,
            "analysis_id": analysis.id,
            "measurements_created": measurements_created,
        },
        status=status.HTTP_201_CREATED
    )