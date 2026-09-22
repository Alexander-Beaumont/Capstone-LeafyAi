"""Django-owned Camera scheduler entry points."""

from __future__ import annotations

from .camera_collector import CameraCollector
from .config import SETTINGS
from .repository import DjangoCameraRepository


def build_collector() -> CameraCollector:
    return CameraCollector(
        DjangoCameraRepository(),
        timezone_name=SETTINGS.timezone_name,
        jpeg_quality=SETTINGS.jpeg_quality,
        warmup_frames=SETTINGS.warmup_frames,
        default_rtsp_username=SETTINGS.default_rtsp_username,
        default_rtsp_password=SETTINGS.default_rtsp_password,
    )


def capture_due_once() -> int:
    return build_collector().process_all()
