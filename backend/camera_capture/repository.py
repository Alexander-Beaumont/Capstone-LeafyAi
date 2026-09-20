"""Direct Django ORM repository used by CameraCollector."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from django.core.files.base import ContentFile
from django.utils import timezone
from telemetry.models import Camera, CameraImage
from camera_capture.serializers import CameraSerializer


class DjangoCameraRepository:
    def get_cameras(self) -> list[dict[str, Any]]:
        rows = Camera.objects.filter(is_archived=False).select_related("farm_level").order_by("id")
        return list(CameraSerializer(rows, many=True).data)

    def get_camera(self, camera_id: Any) -> dict[str, Any]:
        camera = Camera.objects.select_related("farm_level").get(id=camera_id)
        return dict(CameraSerializer(camera).data)

    def get_latest_image(self, camera_id: Any) -> dict[str, Any] | None:
        image = CameraImage.objects.filter(camera_id=camera_id).order_by("-captured_at", "-id").first()
        if image is None:
            return None
        return {
            "image_id": image.id,
            "camera_id": image.camera_id,
            "captured_at": image.captured_at.isoformat(),
            "quality_status": image.quality_status,
            "vlm_ready": image.vlm_ready,
        }

    def upload_official_image(
        self,
        camera_id: Any,
        jpeg_bytes: bytes,
        *,
        captured_at: datetime,
        quality: dict[str, Any],
    ) -> dict[str, Any]:
        if not jpeg_bytes:
            raise ValueError("Official JPEG bytes are empty")
        camera = Camera.objects.get(id=camera_id)
        stamp = captured_at.astimezone(timezone.get_current_timezone()).strftime("%Y%m%dT%H%M%S%f")
        image = CameraImage(
            camera=camera,
            captured_at=captured_at,
            vlm_ready=bool(quality.get("vlm_ready", False)),
            quality_status=str(quality.get("quality_status", "UNKNOWN")).upper(),
            quality_flags=list(quality.get("quality_flags") or []),
            quality_message=str(quality.get("quality_message", "")),
            quality_metrics=dict(quality.get("quality_metrics") or {}),
        )
        image.path.save(f"camera_{camera.id}_{stamp}.jpg", ContentFile(jpeg_bytes), save=True)
        return {
            "image_id": image.id,
            "camera_id": camera.id,
            "captured_at": image.captured_at.isoformat(),
            "image_url": image.path.url,
            "quality_status": image.quality_status,
            "quality_flags": image.quality_flags,
            "quality_message": image.quality_message,
            "vlm_ready": image.vlm_ready,
        }
