from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import cv2


class CameraCaptureError(RuntimeError):
    pass


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
    if isinstance(camera, dict):
        return camera.get(key, default)
    return getattr(camera, key, default)


def build_rtsp_url(camera: Any, *, default_username: str = "", default_password: str = "") -> str:
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
    # MJPG frequently exposes higher USB/laptop webcam modes on Windows.
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
    source_type = str(_value(camera, "source_type", "") or "").upper()

    if source_type == "RTSP":
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp|stimeout;5000000")
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
        # DirectShow is preferable on Windows; OpenCV falls back if unavailable.
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
):
    """Open camera, obtain a fresh BGR frame, and always release the connection."""
    capture = _open_capture(
        camera,
        default_rtsp_username=default_rtsp_username,
        default_rtsp_password=default_rtsp_password,
    )
    try:
        if not capture.isOpened():
            raise CameraCaptureError("Could not open camera source.")

        source_type = str(_value(camera, "source_type", "") or "").upper()
        # Webcams benefit from exposure/focus warmup. For RTSP, a few reads help
        # discard buffered frames while still keeping the connection short-lived.
        reads = max(1, int(warmup_frames)) if source_type == "WEBCAM" else max(2, min(5, int(warmup_frames)))
        frame = None
        ok = False
        for _ in range(reads):
            ok, candidate = capture.read()
            if ok and candidate is not None:
                frame = candidate
        if not ok or frame is None or frame.size == 0:
            raise CameraCaptureError("Camera opened but no valid frame was decoded.")
        return frame
    finally:
        capture.release()
