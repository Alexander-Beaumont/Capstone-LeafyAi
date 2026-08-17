import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from telemetry.models import Camera, CameraImage, Slot

from cv.models import (
    ImageAnalysis,
    PlantVisionMeasurement,
)
from cv.serializers import ImageAnalysisSerializer, PlantVisionMeasurementSerializer

class ImageAnalysisViewSet(viewsets.ModelViewSet):
    queryset = ImageAnalysis.objects.all()
    serializer_class = ImageAnalysisSerializer


class PlantVisionMeasurementViewSet(viewsets.ModelViewSet):
    queryset = PlantVisionMeasurement.objects.all()
    serializer_class = PlantVisionMeasurementSerializer

#Written with AI
@api_view(["POST"])
@transaction.atomic
def ingest_cv_result(request):

    # LeafyCV sends its JSON inside the multipart "metadata" field
    metadata = request.data.get("metadata")

    if not metadata:
        return Response(
            {"error": "metadata is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        data = json.loads(metadata)
    except json.JSONDecodeError:
        return Response(
            {"error": "metadata must contain valid JSON"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # LeafyCV sends the raw JPEG separately
    raw_image = request.FILES.get("raw_image")

    if not raw_image:
        return Response(
            {"error": "raw_image is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    camera_id = data.get("camera_id")

    if not camera_id:
        return Response(
            {"error": "camera_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    analysis_data = data.get("analysis")

    if not analysis_data:
        return Response(
            {"error": "analysis is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    plants = data.get("plants", [])

    # Validate ALL slots before creating anything
    slot_ids = [
        plant.get("slot_id")
        for plant in plants
        if plant.get("slot_id") is not None
    ]

    slots = Slot.objects.filter(
        id__in=slot_ids
    )

    slot_map = {
        str(slot.id): slot
        for slot in slots
    }

    for slot_id in slot_ids:
        if str(slot_id) not in slot_map:
            return Response(
                {
                    "error": f"Unknown slot_id: {slot_id}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    captured_at = data.get("captured_at")

    timestamp = None

    if captured_at:
        timestamp = parse_datetime(captured_at)

    camera_image = CameraImage.objects.create(
        camera=camera,
        path=raw_image,
        **({"timestamp": timestamp} if timestamp else {})
    )

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

    measurement_count = 0
    seen_slots = set()

    for plant in plants:

        slot_id = str(plant["slot_id"])

        # Give a clean error instead of relying only on DB constraint
        if slot_id in seen_slots:
            return Response(
                {
                    "error":
                        f"Duplicate measurement for slot {slot_id}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        seen_slots.add(slot_id)

        slot = slot_map[slot_id]

        PlantVisionMeasurement.objects.create(
            image_analysis=analysis,
            slot=slot,

            canopy_coverage=plant.get(
                "canopy_coverage"
            ),

            width_px=plant.get("width_px"),
            height_px=plant.get("height_px"),

            width_cm=plant.get("width_cm"),
            height_cm=plant.get("height_cm"),

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

    return Response(
        {
            "message": "CV sample stored successfully",
            "image_id": camera_image.id,
            "analysis_id": analysis.id,
            "measurement_count": measurement_count,
        },
        status=status.HTTP_201_CREATED
    )

@api_view(["GET"])
def latest_analysis(request, camera_id):

    camera = get_object_or_404(
        Camera,
        id=camera_id
    )

    analysis = (
        ImageAnalysis.objects
        .filter(image__camera=camera)
        .order_by("-created_at")
        .first()
    )

    if not analysis:
        return Response(
            {"detail": "No analysis found for this camera."},
            status=status.HTTP_404_NOT_FOUND
        )

    measurements = (
        PlantVisionMeasurement.objects
        .filter(image_analysis=analysis)
    )

    return Response({
        "analysis": ImageAnalysisSerializer(
            analysis
        ).data,

        "measurements":
            PlantVisionMeasurementSerializer(
                measurements,
                many=True
            ).data
    })