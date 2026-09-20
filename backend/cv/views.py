import json

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from telemetry.models import Camera, CameraImage
from telemetry.serializers import CameraImageSerializer
from cv.models import ImageAnalysis
from cv.serializers import ImageAnalysisSerializer


class ImageAnalysisViewSet(viewsets.ModelViewSet):
    queryset = ImageAnalysis.objects.select_related("image", "image__camera")
    serializer_class = ImageAnalysisSerializer


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def official_image(request, camera_id):
    """Store one official JPEG captured by the standalone Camera service."""
    camera = get_object_or_404(Camera, id=camera_id)
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"detail": "image is required"}, status=status.HTTP_400_BAD_REQUEST)
    captured_at_value = request.data.get("captured_at")
    captured_at = parse_datetime(str(captured_at_value)) if captured_at_value else timezone.now()
    if captured_at is None:
        return Response({"detail": "captured_at must be a valid ISO 8601 datetime"}, status=status.HTTP_400_BAD_REQUEST)
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


@api_view(["POST"])
def ingest_cv_result(request):
    """Persist one whole-image analysis for an existing CameraImage."""
    data = request.data
    if isinstance(data, dict) and isinstance(data.get("metadata"), str):
        try:
            data = json.loads(data["metadata"])
        except json.JSONDecodeError:
            return Response({"error": "metadata must contain valid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    camera_id, image_id, analysis_data = data.get("camera_id"), data.get("image_id"), data.get("analysis")
    if camera_id is None or image_id is None or not isinstance(analysis_data, dict):
        return Response({"error": "camera_id, image_id, and analysis are required"}, status=status.HTTP_400_BAD_REQUEST)
    camera = get_object_or_404(Camera, id=camera_id)
    image = get_object_or_404(CameraImage, id=image_id, camera=camera)
    if ImageAnalysis.objects.filter(image=image).exists():
        return Response({"error": "This CameraImage has already been analysed"}, status=status.HTTP_409_CONFLICT)
    analysis = ImageAnalysis.objects.create(
        image=image,
        total_canopy_coverage=analysis_data.get("total_canopy_coverage"),
        growth_change=analysis_data.get("growth_change"),
        crowding_percentage=analysis_data.get("crowding_percentage"),
        green_percentage=analysis_data.get("green_percentage"),
        yellow_percentage=analysis_data.get("yellow_percentage"),
        measurement_valid=analysis_data.get("measurement_valid", True),
        processing_time_ms=analysis_data.get("processing_time_ms"),
        vlm_ready=analysis_data.get("vlm_ready", False),
        quality_status=analysis_data.get("quality_status", "UNKNOWN"),
        quality_flags=analysis_data.get("quality_flags", []),
        quality_message=analysis_data.get("quality_message", ""),
    )
    return Response({"message": "CV analysis stored successfully", "image_id": image.id, "analysis_id": analysis.id}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def latest_analysis(request, camera_id):
    camera = get_object_or_404(Camera, id=camera_id)
    queryset = ImageAnalysis.objects.filter(image__camera=camera).select_related("image", "image__camera")
    if request.query_params.get("valid") == "true":
        queryset = queryset.filter(measurement_valid=True)
    analysis = queryset.order_by("-image__captured_at", "-id").first()
    if analysis is None:
        return Response({"detail": "No analysis found for this camera."}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        "camera_id": camera.id,
        "image_id": analysis.image_id,
        "captured_at": analysis.image.captured_at,
        "image": CameraImageSerializer(analysis.image, context={"request": request}).data,
        "analysis": ImageAnalysisSerializer(analysis, context={"request": request}).data,
    })
