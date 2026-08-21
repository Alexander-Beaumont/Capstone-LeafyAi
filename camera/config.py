from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    backend_base_url: str = os.getenv("LEAFY_BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    access_token: str = os.getenv("LEAFY_BACKEND_ACCESS_TOKEN", "")
    refresh_token: str = os.getenv("LEAFY_BACKEND_REFRESH_TOKEN", "")
    timeout_seconds: float = float(os.getenv("LEAFY_CAMERA_HTTP_TIMEOUT", "15"))
    poll_seconds: float = float(os.getenv("LEAFY_CAMERA_POLL_SECONDS", "30"))
    timezone_name: str = os.getenv("LEAFY_CAMERA_TIMEZONE", "Australia/Melbourne")
    jpeg_quality: int = int(os.getenv("LEAFY_CAMERA_JPEG_QUALITY", "92"))
    warmup_frames: int = int(os.getenv("LEAFY_CAMERA_WARMUP_FRAMES", "12"))
    default_rtsp_username: str = os.getenv("FARM_CAMERA_USER", "")
    default_rtsp_password: str = os.getenv("FARM_CAMERA_PASSWORD", "")


SETTINGS = Settings()
