from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from PIL import Image, UnidentifiedImageError

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response

from telemetry.models import Camera, CameraImage
from telemetry.serializers import CameraImageSerializer
from cv.models import ImageAnalysis
from cv.serializers import ImageAnalysisSerializer


class ImageAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    # Analyses may only be created through /api/cv/ingest/ so identity and
    # duplicate checks cannot be bypassed by generic CRUD.
    queryset = ImageAnalysis.objects.select_related("image", "image__camera").order_by("-created_at")
    serializer_class = ImageAnalysisSerializer


def _image_url(request, image: CameraImage) -> str:
    serializer = CameraImageSerializer(image, context={"request": request})
    data = serializer.data
    value = data.get("path")
    return str(value) if value else ""


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def official_image(request, camera_id):
    """Store exactly one validated official JPEG captured by Camera service."""
    camera = get_object_or_404(Camera, id=camera_id)
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"detail": "image is required"}, status=status.HTTP_400_BAD_REQUEST)

    captured_at_value = request.data.get("captured_at")
    if not captured_at_value:
        # Scheduling and growth history depend on the real capture moment, so
        # silently substituting Backend receipt time would corrupt semantics.
        return Response({"detail": "captured_at is required"}, status=status.HTTP_400_BAD_REQUEST)
    captured_at = parse_datetime(str(captured_at_value))
    if captured_at is None:
        return Response({"detail": "captured_at must be a valid ISO 8601 datetime"}, status=status.HTTP_400_BAD_REQUEST)
    if timezone.is_naive(captured_at):
        return Response({"detail": "captured_at must include a timezone offset"}, status=status.HTTP_400_BAD_REQUEST)

    max_bytes = int(os.getenv("LEAFY_MAX_OFFICIAL_IMAGE_BYTES", str(15 * 1024 * 1024)))
    if image_file.size <= 0 or image_file.size > max_bytes:
        return Response(
            {"detail": f"JPEG file size must be between 1 and {max_bytes} bytes"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            image_format = (img.format or "").upper()
            img.verify()
        image_file.seek(0)
    except (UnidentifiedImageError, OSError, ValueError):
        return Response({"detail": "image must contain a decodable JPEG"}, status=status.HTTP_400_BAD_REQUEST)

    if image_format != "JPEG":
        return Response({"detail": "official image must be JPEG"}, status=status.HTTP_400_BAD_REQUEST)

    image = CameraImage.objects.create(camera=camera, captured_at=captured_at, path=image_file)
    return Response(
        {
            "image_id": image.id,
            "camera_id": camera.id,
            "captured_at": image.captured_at,
            "image_url": _image_url(request, image),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def latest_image(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    image = CameraImage.objects.filter(camera=camera).order_by("-captured_at", "-id").first()
    if image is None:
        return Response({"detail": "No image found for this camera."}, status=status.HTTP_404_NOT_FOUND)
    return Response(
        {
            "image_id": image.id,
            "camera_id": camera.id,
            "captured_at": image.captured_at,
            "image_url": _image_url(request, image),
        }
    )


def _percentage(value, field_name: str):
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be numeric or null")
    if parsed < 0 or parsed > 100:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return parsed


def _optional_number(value, field_name: str):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be numeric or null")


@api_view(["POST"])
@parser_classes([JSONParser])
def ingest_cv_result(request):
    """Persist one JSON analysis for an existing official CameraImage."""
    data = request.data
    if not isinstance(data, dict):
        return Response({"error": "JSON object required"}, status=status.HTTP_400_BAD_REQUEST)

    camera_id = data.get("camera_id")
    image_id = data.get("image_id")
    analysis_data = data.get("analysis")
    if camera_id is None or image_id is None or not isinstance(analysis_data, dict):
        return Response(
            {"error": "camera_id, image_id, and analysis are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    camera = get_object_or_404(Camera, id=camera_id)
    image = get_object_or_404(CameraImage, id=image_id)
    if image.camera_id != camera.id:
        return Response(
            {"error": "CameraImage does not belong to camera_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if ImageAnalysis.objects.filter(image=image).exists():
        return Response(
            {"error": "This CameraImage has already been analysed"},
            status=status.HTTP_409_CONFLICT,
        )

    try:
        total_canopy = _percentage(analysis_data.get("total_canopy_coverage"), "total_canopy_coverage")
        crowding = _percentage(analysis_data.get("crowding_percentage"), "crowding_percentage")
        green = _percentage(analysis_data.get("green_percentage"), "green_percentage")
        yellow = _percentage(analysis_data.get("yellow_percentage"), "yellow_percentage")
        growth_change = _optional_number(analysis_data.get("growth_change"), "growth_change")
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    measurement_valid = bool(analysis_data.get("measurement_valid", True))
    if not measurement_valid:
        # A rejected frame must never become a temporal-growth baseline.
        growth_change = None

    quality_status = str(analysis_data.get("quality_status", "UNKNOWN")).upper()
    if quality_status not in {"PASS", "FAIL", "UNKNOWN"}:
        return Response(
            {"error": "quality_status must be PASS, FAIL or UNKNOWN"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    quality_flags = analysis_data.get("quality_flags", [])
    if not isinstance(quality_flags, list):
        return Response({"error": "quality_flags must be a JSON array"}, status=status.HTTP_400_BAD_REQUEST)

    processing_time_ms = analysis_data.get("processing_time_ms")
    if processing_time_ms is not None:
        try:
            processing_time_ms = int(processing_time_ms)
        except (TypeError, ValueError):
            return Response({"error": "processing_time_ms must be an integer or null"}, status=status.HTTP_400_BAD_REQUEST)
        if processing_time_ms < 0:
            return Response({"error": "processing_time_ms cannot be negative"}, status=status.HTTP_400_BAD_REQUEST)

    analysis = ImageAnalysis.objects.create(
        image=image,
        total_canopy_coverage=total_canopy,
        growth_change=growth_change,
        crowding_percentage=crowding,
        green_percentage=green,
        yellow_percentage=yellow,
        measurement_valid=measurement_valid,
        processing_time_ms=processing_time_ms,
        vlm_ready=bool(analysis_data.get("vlm_ready", False)),
        quality_status=quality_status,
        quality_flags=quality_flags,
        quality_message=str(analysis_data.get("quality_message", "")),
    )
    return Response(
        {
            "message": "CV analysis stored successfully",
            "camera_id": camera.id,
            "image_id": image.id,
            "analysis_id": analysis.id,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def latest_analysis(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    queryset = ImageAnalysis.objects.filter(image__camera=camera).select_related("image", "image__camera")
    if request.query_params.get("valid") == "true":
        queryset = queryset.filter(measurement_valid=True)
    analysis = queryset.order_by("-image__captured_at", "-id").first()
    if analysis is None:
        return Response({"detail": "No analysis found for this camera."}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "camera_id": camera.id,
            "image_id": analysis.image_id,
            "captured_at": analysis.image.captured_at,
            "image_url": _image_url(request, analysis.image),
            "analysis": ImageAnalysisSerializer(analysis, context={"request": request}).data,
        }
    )
