import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from telemetry.models import (
    Camera,
    CameraImage,
    Slot,
)

from cv.models import (
    ImageAnalysis,
    PlantVisionMeasurement,
)

from cv.serializers import (
    ImageAnalysisSerializer,
    PlantVisionMeasurementSerializer,
)


# ============================================================
# STANDARD CRUD VIEWSETS
# ============================================================

class ImageAnalysisViewSet(viewsets.ModelViewSet):
    queryset = ImageAnalysis.objects.all()
    serializer_class = ImageAnalysisSerializer


class PlantVisionMeasurementViewSet(viewsets.ModelViewSet):
    queryset = PlantVisionMeasurement.objects.all()
    serializer_class = PlantVisionMeasurementSerializer


# ============================================================
# LEAFYCV INGEST
# POST /api/cv/ingest/
# ============================================================

# Written with AI assistance
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def ingest_cv_result(request):
    """
    Receives one completed LeafyCV analysis.

    Expected multipart/form-data:

        metadata = JSON string
        raw_image = JPEG file

    The metadata contains:
        camera_id
        captured_at
        analysis
        plants

    Creates:
        1 CameraImage
        1 ImageAnalysis
        N PlantVisionMeasurement records
    """

    # --------------------------------------------------------
    # 1. Validate metadata
    # --------------------------------------------------------

    metadata = request.data.get("metadata")

    if not metadata:
        return Response(
            {
                "error": "metadata is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        data = json.loads(metadata)
    except (json.JSONDecodeError, TypeError):
        return Response(
            {
                "error": "metadata must contain valid JSON"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 2. Validate raw image
    # --------------------------------------------------------

    raw_image = request.FILES.get("raw_image")

    if not raw_image:
        return Response(
            {
                "error": "raw_image is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 3. Validate camera
    # --------------------------------------------------------

    camera_id = data.get("camera_id")

    if camera_id is None:
        return Response(
            {
                "error": "camera_id is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    # --------------------------------------------------------
    # 4. Validate analysis section
    # --------------------------------------------------------

    analysis_data = data.get("analysis")

    if not analysis_data:
        return Response(
            {
                "error": "analysis is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 5. Validate captured_at
    # --------------------------------------------------------

    captured_at = data.get("captured_at")

    if not captured_at:
        return Response(
            {
                "error": "captured_at is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    timestamp = parse_datetime(captured_at)

    if timestamp is None:
        return Response(
            {
                "error":
                    "captured_at must be a valid ISO 8601 datetime"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 6. Validate plant measurements
    # --------------------------------------------------------

    plants = data.get("plants", [])

    if not isinstance(plants, list):
        return Response(
            {
                "error": "plants must be a list"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    slot_ids = []

    for plant in plants:

        if not isinstance(plant, dict):
            return Response(
                {
                    "error":
                        "Each item in plants must be an object"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        slot_id = plant.get("slot_id")

        if slot_id is None:
            return Response(
                {
                    "error":
                        "Every plant measurement requires slot_id"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        slot_ids.append(str(slot_id))

    # --------------------------------------------------------
    # 7. Prevent duplicate SLOT measurements
    # --------------------------------------------------------

    if len(slot_ids) != len(set(slot_ids)):
        return Response(
            {
                "error":
                    "Duplicate slot_id in measurements"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 8. Check that every SLOT actually exists
    # --------------------------------------------------------

    try:
        slots = Slot.objects.filter(
            id__in=slot_ids
        )
    except (ValueError, TypeError):
        return Response(
            {
                "error": "One or more slot IDs are invalid"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    slot_map = {
        str(slot.id): slot
        for slot in slots
    }

    for slot_id in slot_ids:

        if slot_id not in slot_map:
            return Response(
                {
                    "error":
                        f"Unknown slot_id: {slot_id}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # ========================================================
    # ALL VALIDATION ABOVE THIS POINT
    #
    # Database writes only begin after the complete request
    # has passed validation.
    # ========================================================

    # --------------------------------------------------------
    # 9. Save raw CameraImage
    # --------------------------------------------------------

    camera_image = CameraImage.objects.create(
        camera=camera,
        timestamp=timestamp,
        path=raw_image
    )

    # --------------------------------------------------------
    # 10. Create whole-image analysis
    # --------------------------------------------------------

    analysis = ImageAnalysis.objects.create(
        image=camera_image,

        total_canopy_coverage=analysis_data.get(
            "total_canopy_coverage"
        ),

        visible_plant_count=analysis_data.get(
            "visible_plant_count"
        ),

        measurement_valid=analysis_data.get(
            "measurement_valid",
            True
        ),

        processing_time_ms=analysis_data.get(
            "processing_time_ms"
        ),
    )

    # --------------------------------------------------------
    # 11. Create per-SLOT measurements
    # --------------------------------------------------------

    measurement_count = 0

    for plant in plants:

        slot_id = str(
            plant["slot_id"]
        )

        slot = slot_map[slot_id]

        PlantVisionMeasurement.objects.create(
            image_analysis=analysis,
            slot=slot,

            canopy_coverage=plant.get(
                "canopy_coverage"
            ),

            width_px=plant.get(
                "width_px"
            ),

            height_px=plant.get(
                "height_px"
            ),

            width_cm=plant.get(
                "width_cm"
            ),

            height_cm=plant.get(
                "height_cm"
            ),

            green_percentage=plant.get(
                "green_percentage"
            ),

            yellow_percentage=plant.get(
                "yellow_percentage"
            ),

            crowding_percentage=plant.get(
                "crowding_percentage"
            ),

            growth_stage=plant.get(
                "growth_stage"
            ),

            growth_change=plant.get(
                "growth_change"
            ),

            visible=plant.get(
                "visible",
                True
            ),

            measurement_valid=plant.get(
                "measurement_valid",
                True
            ),
        )

        measurement_count += 1

    # --------------------------------------------------------
    # 12. Successful response
    # --------------------------------------------------------

    return Response(
        {
            "message":
                "CV sample stored successfully",

            "image_id":
                camera_image.id,

            "analysis_id":
                analysis.id,

            "measurement_count":
                measurement_count,
        },
        status=status.HTTP_201_CREATED
    )


# ============================================================
# LATEST CAMERA ANALYSIS
# GET /api/cv/cameras/<camera_id>/latest-analysis/
# ============================================================

@api_view(["GET"])
def latest_analysis(request, camera_id):
    """
    Returns the latest ImageAnalysis for a camera together
    with every PlantVisionMeasurement belonging to it.
    """

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    analysis = (
        ImageAnalysis.objects
        .filter(
            image__camera=camera
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if not analysis:
        return Response(
            {
                "detail":
                    "No analysis found for this camera."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    measurements = (
        PlantVisionMeasurement.objects
        .filter(
            image_analysis=analysis
        )
        .select_related("slot")
    )

    return Response(
        {
            "analysis":
                ImageAnalysisSerializer(
                    analysis
                ).data,

            "measurements":
                PlantVisionMeasurementSerializer(
                    measurements,
                    many=True
                ).data
        },
        status=status.HTTP_200_OK
    )