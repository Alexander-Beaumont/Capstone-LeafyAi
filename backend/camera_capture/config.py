"""Runtime settings for Django-owned RTSP capture."""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    poll_seconds: float = float(os.getenv("LEAFY_CAMERA_POLL_SECONDS", "30"))
    timezone_name: str = os.getenv("LEAFY_CAMERA_TIMEZONE", os.getenv("LEAFY_TIME_ZONE", "Australia/Melbourne"))
    jpeg_quality: int = int(os.getenv("LEAFY_CAMERA_JPEG_QUALITY", "92"))
    warmup_frames: int = int(os.getenv("LEAFY_CAMERA_WARMUP_FRAMES", "12"))
    default_rtsp_username: str = os.getenv("FARM_CAMERA_USER", "")
    default_rtsp_password: str = os.getenv("FARM_CAMERA_PASSWORD", "")


SETTINGS = Settings()
