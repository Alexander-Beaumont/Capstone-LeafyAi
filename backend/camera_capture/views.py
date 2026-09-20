from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from camera_capture.serializers import CameraImageSerializer, CameraSerializer
from telemetry.models import Camera, CameraImage


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def cameras(request):
    """List active Cameras or create a new Camera.

    GET  /api/cameras/
    POST /api/cameras/

    Camera capture itself remains an internal scheduled service operation.
    This endpoint only exposes Camera configuration through the Django API.
    """

    if request.method == "GET":
        queryset = (
            Camera.objects
            .select_related("farm_level")
            .filter(is_archived=False)
            .order_by("id")
        )
        serializer = CameraSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    serializer = CameraSerializer(
        data=request.data,
        context={"request": request},
    )
    if serializer.is_valid():
        camera = serializer.save()
        return Response(
            CameraSerializer(
                camera,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def camera_detail(request, camera_id: int):
    """Retrieve or update one Camera.

    GET   /api/cameras/{id}/
    PUT   /api/cameras/{id}/
    PATCH /api/cameras/{id}/

    Hard delete is intentionally disabled. Archive with PATCH
    ``{"is_archived": true}`` instead.
    """

    camera = get_object_or_404(
        Camera.objects.select_related("farm_level"),
        pk=camera_id,
    )

    if request.method == "GET":
        return Response(
            CameraSerializer(
                camera,
                context={"request": request},
            ).data
        )

    if request.method == "DELETE":
        return Response(
            {
                "detail": (
                    "Hard delete is disabled. Archive the camera with "
                    "PATCH is_archived=true."
                )
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    serializer = CameraSerializer(
        camera,
        data=request.data,
        partial=request.method == "PATCH",
        context={"request": request},
    )
    if serializer.is_valid():
        camera = serializer.save()
        return Response(
            CameraSerializer(
                camera,
                context={"request": request},
            ).data
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def latest_image(request, camera_id: int):
    """Return the latest official Camera image and Frontend quality summary.

    GET /api/cameras/{id}/latest-image/
    """

    camera = get_object_or_404(Camera, pk=camera_id)
    image = (
        CameraImage.objects
        .filter(camera=camera)
        .order_by("-captured_at", "-id")
        .first()
    )
    if image is None:
        return Response(
            {"detail": "No official image is available for this camera."},
            status=status.HTTP_404_NOT_FOUND,
        )

    payload = CameraImageSerializer(
        image,
        context={"request": request},
    ).data
    return Response(
        {
            "image_id": payload["id"],
            "camera_id": payload["camera"],
            "captured_at": payload["captured_at"],
            "image_url": payload["image_url"],
            "quality_status": payload["quality_status"],
            "quality_reason": payload["quality_reason"],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def camera_images(request):
    """List stored Camera images (read-only).

    GET /api/camera-images/
    """

    queryset = (
        CameraImage.objects
        .select_related("camera")
        .all()
        .order_by("-captured_at", "-id")
    )
    serializer = CameraImageSerializer(
        queryset,
        many=True,
        context={"request": request},
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def camera_image_detail(request, image_id: int):
    """Retrieve one stored Camera image (read-only).

    GET /api/camera-images/{id}/
    """

    image = get_object_or_404(
        CameraImage.objects.select_related("camera"),
        pk=image_id,
    )
    serializer = CameraImageSerializer(
        image,
        context={"request": request},
    )
    return Response(serializer.data)
