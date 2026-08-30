from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from telemetry.models import (
    Camera,
    CameraImage,
)

from cv.models import ImageAnalysis


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_image_url(camera_image):
    """
    Return the media URL for a CameraImage.

    Example:
        /media/camera_images/example.jpg
    """

    if not camera_image.path:
        return None

    try:
        return camera_image.path.url
    except ValueError:
        return None


def validate_percentage(value, field_name):
    """
    Percentage fields may be NULL, but when supplied
    they must be between 0 and 100 inclusive.

    Returns:
        None if valid
        Error message string if invalid
    """

    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return f"{field_name} must be a number or null"

    if decimal_value < 0 or decimal_value > 100:
        return f"{field_name} must be between 0 and 100"

    return None


# ============================================================
# CV INGEST
#
# POST /api/cv/ingest/
# Content-Type: application/json
# ============================================================

# Written with AI assistance
@api_view(["POST"])
@transaction.atomic
def ingest_cv_result(request):
    """
    Store one LeafyCV analysis for an existing CameraImage.

    Expected JSON:

    {
        "camera_id": 1,
        "image_id": 152,
        "analysis": {
            "total_canopy_coverage": 37.50,
            "growth_change": null,
            "crowding_percentage": 31.40,
            "green_percentage": 86.20,
            "yellow_percentage": 4.80,
            "measurement_valid": true,
            "processing_time_ms": 105,
            "vlm_ready": true,
            "quality_status": "PASS",
            "quality_flags": [],
            "quality_message": "..."
        }
    }

    This endpoint creates ONLY an ImageAnalysis.

    It does NOT create:
        - CameraImage
        - raw images
        - plant measurements
        - SLOT measurements
        - PlantVisionMeasurement records
    """

    # --------------------------------------------------------
    # 1. Validate camera_id
    # --------------------------------------------------------

    camera_id = request.data.get("camera_id")

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
    # 2. Validate image_id
    # --------------------------------------------------------

    image_id = request.data.get("image_id")

    if image_id is None:
        return Response(
            {
                "error": "image_id is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    camera_image = get_object_or_404(
        CameraImage,
        id=image_id
    )

    # --------------------------------------------------------
    # 3. Camera/Image identity check
    #
    # Prevent LeafyCV accidentally attaching an analysis
    # from Camera 1 to an image belonging to Camera 2.
    # --------------------------------------------------------

    if camera_image.camera_id != camera.id:
        return Response(
            {
                "error":
                    "CameraImage does not belong to the supplied camera"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 4. Prevent duplicate analysis for same CameraImage
    #
    # ImageAnalysis.image will also be OneToOneField, but
    # returning a clean 409 is better than exposing a DB error.
    # --------------------------------------------------------

    if ImageAnalysis.objects.filter(
        image=camera_image
    ).exists():

        return Response(
            {
                "error":
                    "An analysis already exists for this CameraImage"
            },
            status=status.HTTP_409_CONFLICT
        )

    # --------------------------------------------------------
    # 5. Validate analysis object
    # --------------------------------------------------------

    analysis_data = request.data.get("analysis")

    if not isinstance(analysis_data, dict):
        return Response(
            {
                "error": "analysis must be a JSON object"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 6. Validate percentage fields
    #
    # These may be null, but if supplied must be 0-100.
    # growth_change is NOT included because it may be
    # negative.
    # --------------------------------------------------------

    percentage_fields = [
        "total_canopy_coverage",
        "crowding_percentage",
        "green_percentage",
        "yellow_percentage",
    ]

    for field_name in percentage_fields:

        error = validate_percentage(
            analysis_data.get(field_name),
            field_name
        )

        if error:
            return Response(
                {
                    "error": error
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    # --------------------------------------------------------
    # 7. Validate quality_flags
    # --------------------------------------------------------

    quality_flags = analysis_data.get(
        "quality_flags",
        []
    )

    if quality_flags is None:
        quality_flags = []

    if not isinstance(quality_flags, list):
        return Response(
            {
                "error":
                    "quality_flags must be a list"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # --------------------------------------------------------
    # 8. Create exactly ONE ImageAnalysis
    # --------------------------------------------------------

    analysis = ImageAnalysis.objects.create(
        image=camera_image,

        total_canopy_coverage=analysis_data.get(
            "total_canopy_coverage"
        ),

        growth_change=analysis_data.get(
            "growth_change"
        ),

        crowding_percentage=analysis_data.get(
            "crowding_percentage"
        ),

        green_percentage=analysis_data.get(
            "green_percentage"
        ),

        yellow_percentage=analysis_data.get(
            "yellow_percentage"
        ),

        measurement_valid=analysis_data.get(
            "measurement_valid",
            True
        ),

        processing_time_ms=analysis_data.get(
            "processing_time_ms"
        ),

        vlm_ready=analysis_data.get(
            "vlm_ready",
            False
        ),

        quality_status=analysis_data.get(
            "quality_status",
            "UNKNOWN"
        ),

        quality_flags=quality_flags,

        quality_message=analysis_data.get(
            "quality_message",
            ""
        ),
    )

    # --------------------------------------------------------
    # 9. Successful response
    # --------------------------------------------------------

    return Response(
        {
            "message":
                "CV analysis stored successfully",

            "analysis_id":
                analysis.id,

            "camera_id":
                camera.id,

            "image_id":
                camera_image.id,
        },
        status=status.HTTP_201_CREATED
    )


# ============================================================
# LATEST OFFICIAL IMAGE
#
# GET /api/cv/cameras/<camera_id>/latest-image/
# ============================================================

@api_view(["GET"])
def latest_image(request, camera_id):
    """
    Return the newest official CameraImage for a Camera.

    Returns 404 when the Camera has no official images.
    """

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    camera_image = (
        CameraImage.objects
        .filter(
            camera=camera
        )
        .order_by(
            "-captured_at",
            "-id"
        )
        .first()
    )

    if camera_image is None:
        return Response(
            {
                "detail":
                    "No official image found for this camera."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        {
            "image_id":
                camera_image.id,

            "camera_id":
                camera.id,

            "captured_at":
                camera_image.captured_at,

            "image_url":
                get_image_url(camera_image),
        },
        status=status.HTTP_200_OK
    )


# ============================================================
# LATEST ANALYSIS
#
# GET /api/cv/cameras/<camera_id>/latest-analysis/
#
# Optional:
# GET /api/cv/cameras/<camera_id>/latest-analysis/?valid=true
# ============================================================

@api_view(["GET"])
def latest_analysis(request, camera_id):
    """
    Return the newest ImageAnalysis for a Camera.

    ?valid=true returns the newest analysis where:
        measurement_valid=True

    Image and analysis data are returned together so consumers
    cannot accidentally combine an analysis with a different
    CameraImage.
    """

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    analyses = (
        ImageAnalysis.objects
        .filter(
            image__camera=camera
        )
        .select_related(
            "image"
        )
    )

    # --------------------------------------------------------
    # Optional valid=true filter
    # --------------------------------------------------------

    valid_only = (
        request.query_params
        .get("valid", "")
        .lower()
    )

    if valid_only == "true":
        analyses = analyses.filter(
            measurement_valid=True
        )

    # Newest by actual image capture time.
    analysis = (
        analyses
        .order_by(
            "-image__captured_at",
            "-id"
        )
        .first()
    )

    if analysis is None:

        if valid_only == "true":
            detail = (
                "No valid analysis found for this camera."
            )
        else:
            detail = (
                "No analysis found for this camera."
            )

        return Response(
            {
                "detail": detail
            },
            status=status.HTTP_404_NOT_FOUND
        )

    camera_image = analysis.image

    # --------------------------------------------------------
    # Atomic response
    #
    # camera_id, image_id, captured_at and image_url all come
    # from the SAME CameraImage as this analysis.
    # --------------------------------------------------------

    return Response(
        {
            "camera_id":
                camera.id,

            "image_id":
                camera_image.id,

            "captured_at":
                camera_image.captured_at,

            "image_url":
                get_image_url(camera_image),

            "analysis": {
                "total_canopy_coverage":
                    analysis.total_canopy_coverage,

                "growth_change":
                    analysis.growth_change,

                "crowding_percentage":
                    analysis.crowding_percentage,

                "green_percentage":
                    analysis.green_percentage,

                "yellow_percentage":
                    analysis.yellow_percentage,

                "measurement_valid":
                    analysis.measurement_valid,

                "processing_time_ms":
                    analysis.processing_time_ms,

                "vlm_ready":
                    analysis.vlm_ready,

                "quality_status":
                    analysis.quality_status,

                "quality_flags":
                    analysis.quality_flags,

                "quality_message":
                    analysis.quality_message,
            }
        },
        status=status.HTTP_200_OK
    )