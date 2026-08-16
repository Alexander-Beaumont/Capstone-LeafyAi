from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import quote

import cv2
import numpy as np

OPEN_TIMEOUT_SECONDS = 5.0
READ_TIMEOUT_SECONDS = 8.0
WARMUP_FRAMES = 3


def _build_rtsp_url(camera: dict) -> str:
    rtsp = camera.get("rtsp") or {}
    ip = str(rtsp.get("ip_address") or "").strip()
    port = int(rtsp.get("port", 554))
    path = str(rtsp.get("path") or "").strip()
    username_env = str(rtsp.get("username_env") or "FARM_CAMERA_USER")
    password_env = str(rtsp.get("password_env") or "FARM_CAMERA_PASSWORD")
    username = os.getenv(username_env, "")
    password = os.getenv(password_env, "")

    if not ip:
        raise RuntimeError("RTSP camera IP address is not configured.")
    if not username or not password:
        raise RuntimeError(
            f"RTSP credentials are missing. Set {username_env} and {password_env} in the local environment."
        )
    if path and not path.startswith("/"):
        path = "/" + path

    return (
        f"rtsp://{quote(username, safe='')}:{quote(password, safe='')}"
        f"@{ip}:{port}{path}"
    )


def _capture_rtsp(camera: dict) -> np.ndarray:
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        "rtsp_transport;tcp"
        f"|stimeout;{int(OPEN_TIMEOUT_SECONDS * 1_000_000)}"
    )
    capture: cv2.VideoCapture | None = None
    try:
        capture = cv2.VideoCapture(_build_rtsp_url(camera), cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not capture.isOpened():
            raise ConnectionError("Could not open the RTSP camera.")

        deadline = time.monotonic() + READ_TIMEOUT_SECONDS
        latest: np.ndarray | None = None
        successful = 0
        while time.monotonic() < deadline:
            ok, frame = capture.read()
            if ok and frame is not None and frame.size > 0:
                latest = frame
                successful += 1
                if successful >= WARMUP_FRAMES:
                    return latest
            else:
                time.sleep(0.05)
        if latest is not None:
            return latest
        raise TimeoutError("RTSP opened but no frame was decoded.")
    finally:
        if capture is not None:
            capture.release()


def _capture_webcam(camera: dict) -> np.ndarray:
    index = int(camera.get("webcam_index", 0))

    backends: list[int | None]
    if os.name == "nt":
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]
    else:
        backends = [None]

    last_error = ""
    for backend in backends:
        capture: cv2.VideoCapture | None = None
        try:
            capture = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
            if not capture.isOpened():
                last_error = f"Webcam index {index} could not be opened."
                continue

            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            latest: np.ndarray | None = None
            for _ in range(WARMUP_FRAMES + 2):
                ok, frame = capture.read()
                if ok and frame is not None and frame.size > 0:
                    latest = frame
                time.sleep(0.03)
            if latest is not None:
                return latest
            last_error = f"Webcam index {index} opened but did not return a frame."
        finally:
            if capture is not None:
                capture.release()

    raise ConnectionError(last_error or f"Could not capture from webcam index {index}.")


def _capture_file(camera: dict) -> np.ndarray:
    path = Path(str(camera.get("file_path") or ""))
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {path}")
    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if frame is None or frame.size == 0:
        raise RuntimeError(f"Could not decode image file: {path}")
    return frame


def capture_frame(config: dict) -> np.ndarray:
    """Capture one fresh frame and release the source immediately."""
    camera = config["camera"]
    if not bool(camera.get("enabled", True)):
        raise RuntimeError("This camera is disabled in the LeafyCV configuration.")

    source_type = str(camera.get("source_type", "")).upper()
    if source_type == "RTSP":
        return _capture_rtsp(camera)
    if source_type == "WEBCAM":
        return _capture_webcam(camera)
    if source_type == "FILE":
        return _capture_file(camera)
    raise ValueError(f"Unsupported camera source_type: {source_type}")


def source_description(config: dict) -> str:
    camera = config["camera"]
    source_type = str(camera.get("source_type", "")).upper()
    if source_type == "WEBCAM":
        return f"WEBCAM index {int(camera.get('webcam_index', 0))}"
    if source_type == "RTSP":
        rtsp = camera.get("rtsp") or {}
        return f"RTSP {rtsp.get('ip_address')}:{int(rtsp.get('port', 554))}"
    if source_type == "FILE":
        return f"FILE {camera.get('file_path')}"
    return source_type


def open_live_capture(config: dict) -> cv2.VideoCapture:
    """Open a persistent camera connection for a bounded live test.

    Production/scheduled LeafyCV uses capture_frame(), which opens, captures and
    releases the source for every saved analysis. This helper exists only for
    interactive live testing/calibration.
    """
    camera = config["camera"]
    if not bool(camera.get("enabled", True)):
        raise RuntimeError("This camera is disabled in the LeafyCV configuration.")

    source_type = str(camera.get("source_type", "")).upper()
    if source_type == "FILE":
        raise ValueError("Live testing requires a WEBCAM or RTSP source, not FILE.")

    if source_type == "RTSP":
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;tcp"
            f"|stimeout;{int(OPEN_TIMEOUT_SECONDS * 1_000_000)}"
        )
        capture = cv2.VideoCapture(_build_rtsp_url(camera), cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not capture.isOpened():
            capture.release()
            raise ConnectionError("Could not open the RTSP camera for live testing.")
        return capture

    if source_type == "WEBCAM":
        index = int(camera.get("webcam_index", 0))
        backends: list[int | None] = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None] if os.name == "nt" else [None]
        last_error = ""
        for backend in backends:
            capture = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
            if capture.isOpened():
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return capture
            capture.release()
            last_error = f"Webcam index {index} could not be opened."
        raise ConnectionError(last_error or f"Could not open webcam index {index}.")

    raise ValueError(f"Unsupported camera source_type for live testing: {source_type}")


def read_live_frame(capture: cv2.VideoCapture, timeout_seconds: float = 3.0) -> np.ndarray:
    """Read one current frame from an already-open live capture."""
    deadline = time.monotonic() + max(0.2, float(timeout_seconds))
    latest: np.ndarray | None = None
    while time.monotonic() < deadline:
        ok, frame = capture.read()
        if ok and frame is not None and frame.size > 0:
            latest = frame
            break
        time.sleep(0.02)
    if latest is None:
        raise TimeoutError("The live camera is open but did not return a frame.")
    return latest
