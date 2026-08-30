"""Camera acquisition helpers.

This module owns only RTSP/WEBCAM capture and JPEG encoding.  It never imports
Django and never performs computer vision.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import cv2
import numpy as np


class CameraCaptureError(RuntimeError):
    """Raised when an official frame cannot be acquired."""


# Common webcam modes are attempted from highest to lowest.  This is useful for
# laptop/USB webcam development and does not affect RTSP farm cameras.
COMMON_WEBCAM_RESOLUTIONS = [
    (3840, 2160),
    (2560, 1440),
    (1920, 1080),
    (1600, 1200),
    (1280, 1024),
    (1280, 960),
    (1280, 720),
    (1024, 768),
    (800, 600),
    (640, 480),
]


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
    CAMERA_<id>_PASSWORD.  If they do not exist, FARM_CAMERA_USER/PASSWORD are
    used as defaults by the caller.
    """
    ip_address = _value(camera, "ip_address")
    if not ip_address:
        raise CameraCaptureError("RTSP camera requires ip_address.")

    port = int(_value(camera, "rtsp_port", 554) or 554)
    path = str(_value(camera, "rtsp_path", "/stream1") or "/stream1")
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


def _try_best_webcam_resolution(capture: cv2.VideoCapture) -> tuple[int, int]:
    """Ask a local webcam for the best common resolution it accepts."""
    # MJPG often exposes higher USB camera resolutions on Windows.
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

    for width, height in COMMON_WEBCAM_RESOLUTIONS:
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if actual_width == width and actual_height == height:
            return actual_width, actual_height

    return (
        int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )


def _open_capture(
    camera: Any,
    *,
    default_rtsp_username: str = "",
    default_rtsp_password: str = "",
) -> cv2.VideoCapture:
    """Open an RTSP or WEBCAM source according to backend Camera config."""
    source_type = str(_value(camera, "source_type", "") or "").upper()

    if source_type == "RTSP":
        # TCP is preferred for stable official captures.  Buffer size is kept
        # small so the service is less likely to read an old buffered frame.
        os.environ.setdefault(
            "OPENCV_FFMPEG_CAPTURE_OPTIONS",
            "rtsp_transport;tcp|stimeout;5000000",
        )
        url = build_rtsp_url(
            camera,
            default_username=default_rtsp_username,
            default_password=default_rtsp_password,
        )
        capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return capture

    if source_type == "WEBCAM":
        index = _value(camera, "webcam_index")
        if index is None:
            raise CameraCaptureError("WEBCAM camera requires webcam_index.")

        # DirectShow is normally more reliable on Windows.  Fall back to the
        # default OpenCV backend if DirectShow cannot open the device.
        if os.name == "nt":
            capture = cv2.VideoCapture(int(index), cv2.CAP_DSHOW)
            if not capture.isOpened():
                capture.release()
                capture = cv2.VideoCapture(int(index))
        else:
            capture = cv2.VideoCapture(int(index))

        if capture.isOpened():
            _try_best_webcam_resolution(capture)
        return capture

    raise CameraCaptureError(f"Unsupported source_type: {source_type!r}")


def capture_fresh_frame(
    camera: Any,
    *,
    warmup_frames: int = 12,
    default_rtsp_username: str = "",
    default_rtsp_password: str = "",
) -> np.ndarray:
    """Open the source, discard stale/warm-up frames, return one fresh BGR frame.

    The connection is always released before this function returns.  For RTSP
    sources only a few frames are read to clear buffering; webcams use more
    warm-up frames so auto exposure/focus can settle.
    """
    capture = _open_capture(
        camera,
        default_rtsp_username=default_rtsp_username,
        default_rtsp_password=default_rtsp_password,
    )

    try:
        if not capture.isOpened():
            raise CameraCaptureError("Could not open camera source.")

        source_type = str(_value(camera, "source_type", "") or "").upper()
        reads = (
            max(1, int(warmup_frames))
            if source_type == "WEBCAM"
            else max(2, min(5, int(warmup_frames)))
        )

        frame: np.ndarray | None = None
        ok = False
        for _ in range(reads):
            ok, candidate = capture.read()
            if ok and candidate is not None and candidate.size > 0:
                frame = candidate

        if not ok or frame is None or frame.size == 0:
            raise CameraCaptureError("Camera opened but no valid frame was decoded.")

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
