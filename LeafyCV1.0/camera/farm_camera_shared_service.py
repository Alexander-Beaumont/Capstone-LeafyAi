#!/usr/bin/env python3
"""Single shared farm-camera service for a near-live dashboard.

Run ONE copy of this service per camera on the backend/shared machine.
It opens one RTSP connection, keeps the newest decoded frame, publishes an
atomic latest JPEG, and serves the same frames to dashboard browsers.

This follows the project-owner's recommended shared snapshot architecture.
Do not run one copy per dashboard user/student.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

import cv2


@dataclass(frozen=True)
class Camera:
    name: str
    ip: str
    port: int = 554


CAMERAS = {
    "level1_camera1": Camera("level1_camera1", os.getenv("FARM_CAMERA1_IP", "")),
    "level1_camera2": Camera("level1_camera2", os.getenv("FARM_CAMERA2_IP", "")),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("camera", choices=CAMERAS.keys())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--publish-fps",
        type=float,
        default=1.0,
        help="Near-live JPEG update rate. Default: 1 fps.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("shared_camera"),
    )
    parser.add_argument("--jpeg-quality", type=int, default=85)
    return parser.parse_args()


def build_rtsp_url(camera: Camera) -> str:
    if not camera.ip:
        raise RuntimeError(
            f"Set the IP environment variable for {camera.name} before running."
        )
    username = os.getenv("FARM_CAMERA_USER", "")
    password = os.getenv("FARM_CAMERA_PASSWORD", "")
    path = os.getenv("FARM_CAMERA_RTSP_PATH", "")

    if not username or not password:
        raise RuntimeError(
            "Set FARM_CAMERA_USER and FARM_CAMERA_PASSWORD before running."
        )

    if path and not path.startswith("/"):
        path = "/" + path

    return (
        f"rtsp://{quote(username, safe='')}:{quote(password, safe='')}"
        f"@{camera.ip}:{camera.port}{path}"
    )


class SharedFrameState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jpeg: bytes | None = None
        self.sequence = 0
        self.captured_at: str | None = None
        self.error: str | None = None
        self.stop = threading.Event()

    def publish(self, jpeg: bytes) -> None:
        with self.lock:
            self.jpeg = jpeg
            self.sequence += 1
            self.captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
            self.error = None

    def set_error(self, error: str) -> None:
        with self.lock:
            self.error = error

    def snapshot(self):
        with self.lock:
            return self.jpeg, self.sequence, self.captured_at, self.error


class CameraWorker(threading.Thread):
    def __init__(
        self,
        camera: Camera,
        state: SharedFrameState,
        output_path: Path,
        publish_fps: float,
        jpeg_quality: int,
    ) -> None:
        super().__init__(daemon=True)
        self.camera = camera
        self.state = state
        self.output_path = output_path
        self.publish_interval = 1.0 / max(0.1, publish_fps)
        self.jpeg_quality = max(40, min(100, jpeg_quality))

    def atomic_write(self, data: bytes) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.output_path.with_suffix(self.output_path.suffix + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, self.output_path)

    def run(self) -> None:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;tcp|stimeout;5000000"
        )

        while not self.state.stop.is_set():
            capture = None
            try:
                capture = cv2.VideoCapture(
                    build_rtsp_url(self.camera),
                    cv2.CAP_FFMPEG,
                )
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not capture.isOpened():
                    raise ConnectionError(
                        f"Could not open {self.camera.name} at "
                        f"{self.camera.ip}:{self.camera.port}"
                    )

                print(
                    f"Shared service connected to {self.camera.name} "
                    f"({self.camera.ip})."
                )
                next_publish = 0.0

                while not self.state.stop.is_set():
                    ok, frame = capture.read()
                    if not ok or frame is None:
                        raise RuntimeError("RTSP frame read failed")

                    now = time.monotonic()
                    if now < next_publish:
                        continue

                    success, encoded = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality],
                    )
                    if not success:
                        continue

                    jpeg = encoded.tobytes()
                    self.atomic_write(jpeg)
                    self.state.publish(jpeg)
                    next_publish = now + self.publish_interval

            except Exception as exc:
                self.state.set_error(str(exc))
                print(f"Camera service error: {exc}. Retrying in 2 seconds...")
                self.state.stop.wait(2.0)
            finally:
                if capture is not None:
                    capture.release()

        print("Shared RTSP connection released.")


def make_handler(state: SharedFrameState, camera: Camera):
    class Handler(BaseHTTPRequestHandler):
        server_version = "LeafyAISharedCamera/1.0"

        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Leafy AI Camera</title>
<style>body{{margin:0;background:#111;color:#eee;font-family:Arial}}
main{{max-width:1100px;margin:auto;padding:16px}}img{{width:100%;height:auto;border-radius:8px}}
small{{color:#aaa}}</style></head>
<body><main><h2>Leafy AI - {camera.name}</h2>
<img src='/stream.mjpg' alt='Farm camera'>
<p><small>Shared backend stream. One RTSP connection serves all dashboard viewers.</small></p>
</main></body></html>"""
                body = html.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path.startswith("/latest.jpg"):
                jpeg, _seq, _ts, _error = state.snapshot()
                if jpeg is None:
                    self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "No frame yet")
                    return
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(jpeg)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.end_headers()
                self.wfile.write(jpeg)
                return

            if self.path.startswith("/status"):
                _jpeg, sequence, captured_at, error = state.snapshot()
                body = json.dumps(
                    {
                        "camera": camera.name,
                        "ip": camera.ip,
                        "frame_sequence": sequence,
                        "captured_at": captured_at,
                        "error": error,
                    }
                ).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path.startswith("/stream.mjpg"):
                self.send_response(HTTPStatus.OK)
                self.send_header(
                    "Content-Type",
                    "multipart/x-mixed-replace; boundary=frame",
                )
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                last_sequence = -1
                try:
                    while not state.stop.is_set():
                        jpeg, sequence, _ts, _error = state.snapshot()
                        if jpeg is None or sequence == last_sequence:
                            time.sleep(0.05)
                            continue
                        last_sequence = sequence
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(
                            f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii")
                        )
                        self.wfile.write(jpeg)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return

            self.send_error(HTTPStatus.NOT_FOUND)

    return Handler


def main() -> int:
    args = parse_args()
    if args.publish_fps <= 0:
        raise SystemExit("--publish-fps must be greater than 0")

    camera = CAMERAS[args.camera]
    latest_path = args.output / f"{camera.name}_latest.jpg"
    state = SharedFrameState()
    worker = CameraWorker(
        camera,
        state,
        latest_path,
        args.publish_fps,
        args.jpeg_quality,
    )
    worker.start()

    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_handler(state, camera),
    )

    print(f"Dashboard camera page: http://{args.host}:{args.port}/")
    print(f"MJPEG endpoint:       http://{args.host}:{args.port}/stream.mjpg")
    print(f"Latest JPEG:          {latest_path}")
    print("Press Ctrl+C to turn the shared camera service off.")

    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("Stopping shared camera service...")
    finally:
        state.stop.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=8.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
