"""Django-owned Camera scheduler entry points."""
from __future__ import annotations
from .camera_collector import CameraCollector
from .config import SETTINGS
from .lighting_client import LocalLightingController
from .repository import DjangoCameraRepository

def build_collector() -> CameraCollector:
    return CameraCollector(
        DjangoCameraRepository(),
        timezone_name=SETTINGS.timezone_name,
        jpeg_quality=SETTINGS.jpeg_quality,
        warmup_frames=SETTINGS.warmup_frames,
        default_rtsp_username=SETTINGS.default_rtsp_username,
        default_rtsp_password=SETTINGS.default_rtsp_password,
        lighting=LocalLightingController() if SETTINGS.lighting_enabled else None,
        pre_capture_light_on_seconds=SETTINGS.pre_capture_light_on_seconds,
        post_capture_restore_seconds=SETTINGS.post_capture_restore_seconds,
    )

def capture_due_once() -> int:
    return build_collector().process_all()
