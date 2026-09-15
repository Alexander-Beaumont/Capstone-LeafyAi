"""Runtime configuration for Django-owned RTSP camera capture."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)

    if raw is None:
        return default

    return raw.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass(frozen=True)
class Settings:
    poll_seconds: float = float(
        os.getenv(
            "LEAFY_CAMERA_POLL_SECONDS",
            "30",
        )
    )

    background_enabled: bool = _env_bool(
        "LEAFY_CAMERA_BACKGROUND_ENABLED",
        False,
    )

    timezone_name: str = os.getenv(
        "LEAFY_CAMERA_TIMEZONE",
        os.getenv(
            "LEAFY_TIME_ZONE",
            "Australia/Melbourne",
        ),
    )

    jpeg_quality: int = int(
        os.getenv(
            "LEAFY_CAMERA_JPEG_QUALITY",
            "92",
        )
    )

    warmup_frames: int = int(
        os.getenv(
            "LEAFY_CAMERA_WARMUP_FRAMES",
            "12",
        )
    )

    default_rtsp_username: str = os.getenv(
        "FARM_CAMERA_USER",
        "",
    )

    default_rtsp_password: str = os.getenv(
        "FARM_CAMERA_PASSWORD",
        "",
    )

    lighting_enabled: bool = _env_bool(
        "LEAFY_LIGHTING_ENABLED",
        False,
    )

    pre_capture_light_on_seconds: float = float(
        os.getenv(
            "LEAFY_LIGHTING_PRE_CAPTURE_ON_SECONDS",
            "2.0",
        )
    )

    post_capture_restore_seconds: float = float(
        os.getenv(
            "LEAFY_LIGHTING_POST_CAPTURE_DELAY_SECONDS",
            "1.0",
        )
    )


SETTINGS = Settings()