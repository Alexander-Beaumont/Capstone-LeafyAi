"""RTSP camera acquisition helpers.

This module owns only RTSP capture and JPEG encoding. It never imports Django
and never performs computer vision.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import cv2
import numpy as np


class CameraCaptureError(RuntimeError):
    """Raised when an official frame cannot be acquired."""


def _value(camera: Any, key: str, default: Any = None) -> Any:
    """Read a camera field from either a dict or an object."""
    if isinstance(camera, dict):
        return camera.get(key, default)
    return getattr(camera, key, default)


def build_rtsp_url(
    camera: Any,
    *,
    default_username: str = "",
    default_password: str = "",
) -> str:
    """Build the RTSP URL without storing credentials in the database.

    Per-camera credentials can be supplied with CAMERA_<id>_USER and
    CAMERA_<id>_PASSWORD. If they do not exist, FARM_CAMERA_USER/PASSWORD are
    used as defaults by the caller.
    """
    source_type = str(_value(camera, "source_type", "") or "").upper()
    if source_type != "RTSP":
        raise CameraCaptureError("Only RTSP cameras are supported.")

    ip_address = _value(camera, "ip_address")
    if not ip_address:
        raise CameraCaptureError("RTSP camera requires ip_address.")

    port_value = _value(camera, "rtsp_port")
    if port_value in (None, ""):
        raise CameraCaptureError("RTSP camera requires rtsp_port.")
    port = int(port_value)

    path_value = _value(camera, "rtsp_path")
    if not path_value:
        raise CameraCaptureError("RTSP camera requires rtsp_path.")
    path = str(path_value)
    if not path.startswith("/"):
        path = "/" + path

    camera_id = _value(camera, "id", "")
    username = os.getenv(f"CAMERA_{camera_id}_USER", default_username).strip()
    password = os.getenv(f"CAMERA_{camera_id}_PASSWORD", default_password).strip()

    auth = ""
    if username:
        auth = quote(username, safe="")
        if password:
            auth += ":" + quote(password, safe="")
        auth += "@"

    return f"rtsp://{auth}{ip_address}:{port}{path}"


def _open_capture(
    camera: Any,
    *,
    default_rtsp_username: str = "",
    default_rtsp_password: str = "",
) -> cv2.VideoCapture:
    """Open one RTSP source according to Backend Camera config."""
    url = build_rtsp_url(
        camera,
        default_username=default_rtsp_username,
        default_password=default_rtsp_password,
    )

    # TCP is preferred for stable official captures. Keep the buffer small so
    # the service is less likely to read an old buffered frame.
    os.environ.setdefault(
        "OPENCV_FFMPEG_CAPTURE_OPTIONS",
        "rtsp_transport;tcp|stimeout;5000000",
    )
    capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


def capture_fresh_frame(
    camera: Any,
    *,
    warmup_frames: int = 12,
    default_rtsp_username: str = "",
    default_rtsp_password: str = "",
) -> np.ndarray:
    """Open RTSP, discard a few buffered frames, and return one fresh BGR frame."""
    capture = _open_capture(
        camera,
        default_rtsp_username=default_rtsp_username,
        default_rtsp_password=default_rtsp_password,
    )

    try:
        if not capture.isOpened():
            raise CameraCaptureError("Could not open RTSP camera source.")

        reads = max(2, min(5, int(warmup_frames)))
        frame: np.ndarray | None = None
        ok = False
        for _ in range(reads):
            ok, candidate = capture.read()
            if ok and candidate is not None and candidate.size > 0:
                frame = candidate

        if not ok or frame is None or frame.size == 0:
            raise CameraCaptureError("RTSP camera opened but no valid frame was decoded.")

        return frame
    finally:
        capture.release()


def encode_jpeg(frame: np.ndarray, *, jpeg_quality: int = 92) -> bytes:
    """Encode an acquired frame before lighting is restored.

    Encoding before the lighting ON command makes the capture boundary explicit:
    the official frame is already safely represented as JPEG bytes before the
    grow light changes again.
    """
    if frame is None or frame.size == 0:
        raise CameraCaptureError("Cannot encode an empty camera frame.")

    quality = max(50, min(100, int(jpeg_quality)))
    ok, encoded = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), quality],
    )
    if not ok:
        raise CameraCaptureError("Could not encode camera frame as JPEG.")

    return encoded.tobytes()
