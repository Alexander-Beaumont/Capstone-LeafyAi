"""Environment-backed configuration for the standalone Camera service.

Backend camera configuration (RTSP source, schedule, enabled state, ROI, etc.)
stays in Django.  Environment variables in this module are only for service
runtime concerns such as credentials, HTTP timeouts, JPEG quality, and the
optional lighting controller connection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    """Read a conventional true/false environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # ------------------------------------------------------------------
    # Django Backend connection
    # ------------------------------------------------------------------
    backend_base_url: str = os.getenv(
        "LEAFY_BACKEND_BASE_URL", "http://127.0.0.1:8000"
    ).rstrip("/")
    access_token: str = os.getenv("LEAFY_BACKEND_ACCESS_TOKEN", "")
    refresh_token: str = os.getenv("LEAFY_BACKEND_REFRESH_TOKEN", "")
    timeout_seconds: float = float(os.getenv("LEAFY_CAMERA_HTTP_TIMEOUT", "15"))

    # ------------------------------------------------------------------
    # Camera service runtime
    # ------------------------------------------------------------------
    poll_seconds: float = float(os.getenv("LEAFY_CAMERA_POLL_SECONDS", "30"))
    timezone_name: str = os.getenv("LEAFY_CAMERA_TIMEZONE", "Australia/Melbourne")
    jpeg_quality: int = int(os.getenv("LEAFY_CAMERA_JPEG_QUALITY", "92"))
    warmup_frames: int = int(os.getenv("LEAFY_CAMERA_WARMUP_FRAMES", "12"))

    # Default RTSP credentials.  Per-camera environment variables such as
    # CAMERA_1_USER / CAMERA_1_PASSWORD override these values.
    default_rtsp_username: str = os.getenv("FARM_CAMERA_USER", "")
    default_rtsp_password: str = os.getenv("FARM_CAMERA_PASSWORD", "")

    # ------------------------------------------------------------------
    # Optional Camera <-> Lighting/Switch integration
    # ------------------------------------------------------------------
    # When disabled, official capture works exactly as before.
    lighting_enabled: bool = _env_bool("LEAFY_LIGHTING_ENABLED", False)
    lighting_base_url: str = os.getenv("LEAFY_LIGHTING_BASE_URL", "").rstrip("/")
    lighting_state_path: str = os.getenv(
        "LEAFY_LIGHTING_STATE_PATH", "/api/lighting/magenta/state/"
    )
    lighting_access_token: str = os.getenv("LEAFY_LIGHTING_ACCESS_TOKEN", "")
    lighting_timeout_seconds: float = float(os.getenv("LEAFY_LIGHTING_TIMEOUT", "5"))

    # Final MVP capture sequence:
    # OFF -> wait 2 s -> capture + JPEG encode -> wait 1 s -> ON -> upload.
    pre_capture_light_off_seconds: float = float(
        os.getenv("LEAFY_LIGHTING_PRE_CAPTURE_OFF_SECONDS", "2.0")
    )
    post_capture_restore_seconds: float = float(
        os.getenv("LEAFY_LIGHTING_POST_CAPTURE_DELAY_SECONDS", "1.0")
    )
    lighting_require_confirmation: bool = _env_bool(
        "LEAFY_LIGHTING_REQUIRE_CONFIRMATION", True
    )


SETTINGS = Settings()
