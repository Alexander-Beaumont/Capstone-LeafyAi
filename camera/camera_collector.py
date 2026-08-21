from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .backend_client import BackendClient
from .camera_client import capture_fresh_frame


@dataclass
class CaptureDecision:
    due: bool
    reason: str


def _parse_time(value: Any) -> time | None:
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value
    text = str(value)
    try:
        return time.fromisoformat(text)
    except ValueError:
        return None


def _inside_window(now_local: datetime, start: time | None, end: time | None) -> bool:
    if start is None or end is None:
        return True
    current = now_local.time().replace(tzinfo=None)
    if start <= end:
        return start <= current <= end
    # Supports overnight windows such as 20:00-06:00.
    return current >= start or current <= end


def _parse_backend_datetime(value: Any, timezone_name: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    zone = ZoneInfo(timezone_name)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def capture_decision(
    camera: dict[str, Any],
    latest_image: dict[str, Any] | None,
    *,
    now_local: datetime,
    timezone_name: str,
    force: bool = False,
) -> CaptureDecision:
    if not bool(camera.get("enabled", True)):
        return CaptureDecision(False, "camera disabled")
    if not bool(camera.get("cv_enabled", True)):
        return CaptureDecision(False, "CV capture disabled")

    start = _parse_time(camera.get("active_start_time"))
    end = _parse_time(camera.get("active_end_time"))
    if not force and not _inside_window(now_local, start, end):
        return CaptureDecision(False, "outside active hours")

    if force:
        return CaptureDecision(True, "forced capture")

    interval_minutes = max(1, int(camera.get("capture_interval_minutes") or 30))
    if not latest_image:
        return CaptureDecision(True, "no previous official image")

    captured_at = _parse_backend_datetime(
        latest_image.get("captured_at") or latest_image.get("timestamp"),
        timezone_name,
    )
    if captured_at is None:
        return CaptureDecision(True, "latest image timestamp unavailable")

    if now_local >= captured_at + timedelta(minutes=interval_minutes):
        return CaptureDecision(True, f"{interval_minutes}-minute interval elapsed")
    return CaptureDecision(False, "interval not yet elapsed")


class CameraCollector:
    def __init__(
        self,
        backend: BackendClient,
        *,
        timezone_name: str = "Australia/Melbourne",
        jpeg_quality: int = 92,
        warmup_frames: int = 12,
        default_rtsp_username: str = "",
        default_rtsp_password: str = "",
    ) -> None:
        self.backend = backend
        self.timezone_name = timezone_name
        self.zone = ZoneInfo(timezone_name)
        self.jpeg_quality = jpeg_quality
        self.warmup_frames = warmup_frames
        self.default_rtsp_username = default_rtsp_username
        self.default_rtsp_password = default_rtsp_password

    def process_camera(self, camera: dict[str, Any], *, force: bool = False) -> bool:
        camera_id = camera.get("id")
        if camera_id is None:
            print("Skipping camera without id.")
            return False

        latest = self.backend.get_latest_image(camera_id)
        now_local = datetime.now(self.zone)
        decision = capture_decision(
            camera,
            latest,
            now_local=now_local,
            timezone_name=self.timezone_name,
            force=force,
        )
        if not decision.due:
            print(f"Camera {camera_id}: skip ({decision.reason}).")
            return False

        print(f"Camera {camera_id}: capture ({decision.reason}).")
        frame = capture_fresh_frame(
            camera,
            warmup_frames=self.warmup_frames,
            default_rtsp_username=self.default_rtsp_username,
            default_rtsp_password=self.default_rtsp_password,
        )
        height, width = frame.shape[:2]
        response = self.backend.upload_official_image(
            camera_id,
            frame,
            captured_at=now_local,
            jpeg_quality=self.jpeg_quality,
        )
        image_id = response.get("image_id", response.get("id", "?"))
        print(f"Camera {camera_id}: uploaded {width}x{height} JPEG -> CameraImage {image_id}.")
        return True

    def process_all(self, *, camera_id: int | None = None, force: bool = False) -> int:
        if camera_id is not None:
            cameras = [self.backend.get_camera(camera_id)]
        else:
            cameras = self.backend.get_cameras()
        success_count = 0
        for camera in cameras:
            try:
                if self.process_camera(camera, force=force):
                    success_count += 1
            except Exception as exc:
                print(f"Camera {camera.get('id', '?')}: ERROR: {exc}")
        return success_count
