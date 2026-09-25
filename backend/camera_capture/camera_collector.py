"""Official RTSP camera capture scheduling and persistence.

Each Camera is due when its own latest official CameraImage is older than its
`capture_interval_minutes`, subject to the Camera active-hours window. Missed
intervals are never backfilled: an overdue Camera creates at most one image per
collector poll. Multiple due Cameras are processed in the same poll without
changing powerboard or grow-light state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .camera_client import capture_fresh_frame, encode_jpeg
from .quality import assess_image_quality


@dataclass(frozen=True)
class CaptureDecision:
    """Result of deciding whether one Camera needs an official image."""

    due: bool
    reason: str
    due_at: datetime | None = None


def _parse_time(value: Any) -> time | None:
    """Parse a Backend TimeField value; return None when absent/invalid."""
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value
    try:
        return time.fromisoformat(str(value))
    except ValueError:
        return None


def _inside_window(now_local: datetime, start: time | None, end: time | None) -> bool:
    """Return whether ``now_local`` is inside the configured active window.

    Contract:
    - start=None and end=None -> 24-hour operation.
    - start < end -> same-day window, e.g. 06:00 -> 22:00.
    - start > end -> overnight window, e.g. 20:00 -> 06:00.
    - Backend should reject start == end. The defensive fallback here treats it
      as a one-point window rather than crashing.
    """
    current = now_local.time().replace(tzinfo=None)

    if start is None and end is None:
        return True
    if start is not None and end is None:
        return current >= start
    if start is None and end is not None:
        return current <= end

    assert start is not None and end is not None
    if start < end:
        return start <= current <= end
    if start > end:
        return current >= start or current <= end
    return current == start


def _parse_backend_datetime(value: Any, timezone_name: str) -> datetime | None:
    """Convert a Backend ISO timestamp to the Camera service local timezone."""
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

    zone = ZoneInfo(timezone_name)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def capture_decision(
    camera: dict[str, Any],
    latest_image: dict[str, Any] | None,
    *,
    now_local: datetime,
    timezone_name: str,
    force: bool = False,
) -> CaptureDecision:
    """Decide whether one Camera is due using the final latest-image rule.

    The decision order is intentionally simple:
    1. Camera capture must be enabled.
    2. Current time must be inside the Camera's active window.
    3. If no official image exists, capture now.
    4. Otherwise compare elapsed time with capture_interval_minutes.

    Missed intervals are never backfilled. One overdue Camera produces at most
    one new official image in one collector poll.
    """
    if not bool(camera.get("enabled", True)):
        return CaptureDecision(False, "camera disabled")
    if force:
        return CaptureDecision(True, "forced capture", due_at=now_local)
    start = _parse_time(camera.get("active_start_time"))
    end = _parse_time(camera.get("active_end_time"))
    if not _inside_window(now_local, start, end):
        return CaptureDecision(False, "outside active hours")

    if not latest_image:
        return CaptureDecision(True, "no previous official image", due_at=now_local)

    response_camera_id = latest_image.get("camera_id")
    camera_id = camera.get("id", camera.get("camera_id"))
    if (
        response_camera_id is not None
        and camera_id is not None
        and str(response_camera_id) != str(camera_id)
    ):
        raise ValueError(
            f"latest-image camera mismatch: requested Camera {camera_id}, "
            f"received camera_id={response_camera_id}"
        )

    captured_at = _parse_backend_datetime(
        latest_image.get("captured_at"),
        timezone_name,
    )
    if captured_at is None:
        # A malformed/missing timestamp cannot safely prove the interval has
        # been satisfied, so capture one replacement image rather than stall.
        return CaptureDecision(True, "latest image timestamp unavailable", due_at=now_local)

    interval_minutes = max(1, int(camera.get("capture_interval_minutes") or 30))
    due_at = captured_at + timedelta(minutes=interval_minutes)

    if now_local >= due_at:
        return CaptureDecision(True, "capture interval elapsed", due_at=due_at)

    return CaptureDecision(False, "capture interval not elapsed", due_at=due_at)


class CameraCollector:
    """Coordinate scheduling, RTSP capture, quality checks, and persistence."""

    def __init__(
        self,
        backend: Any,
        *,
        timezone_name: str = "Australia/Melbourne",
        jpeg_quality: int = 92,
        warmup_frames: int = 12,
        default_rtsp_username: str = "",
        default_rtsp_password: str = "",
    ) -> None:
        self.backend = backend
        self.timezone_name = timezone_name
        self.zone = ZoneInfo(timezone_name)
        self.jpeg_quality = jpeg_quality
        self.warmup_frames = warmup_frames
        self.default_rtsp_username = default_rtsp_username
        self.default_rtsp_password = default_rtsp_password

    def _capture_and_encode(
        self,
        camera: dict[str, Any],
    ) -> tuple[bytes, datetime, int, int, dict[str, Any]]:
        """Capture one fresh frame, assess it, and encode the official JPEG."""
        frame = capture_fresh_frame(
            camera,
            warmup_frames=self.warmup_frames,
            default_rtsp_username=self.default_rtsp_username,
            default_rtsp_password=self.default_rtsp_password,
        )
        captured_at = datetime.now(self.zone)
        height, width = frame.shape[:2]

        quality = assess_image_quality(
            frame
        )

        jpeg_bytes = encode_jpeg(
            frame,
            jpeg_quality=self.jpeg_quality,
        )

        return (
            jpeg_bytes,
            captured_at,
            width,
            height,
            quality,
        )
    def _upload_capture(
        self,
        camera: dict[str, Any],
        capture: tuple[bytes, datetime, int, int, dict[str, Any]],
    ) -> bool:
        """Persist one already-encoded official capture."""
        camera_id = camera.get("id", camera.get("camera_id"))
        jpeg_bytes, captured_at, width, height, quality = capture

        response = self.backend.upload_official_image(
            camera_id,
            jpeg_bytes,
            captured_at=captured_at,
            quality=quality,
        )

        response_camera_id = response.get("camera_id")
        if (
            response_camera_id is not None
            and str(response_camera_id) != str(camera_id)
        ):
            raise ValueError(
                f"official-image response camera mismatch: sent Camera {camera_id}, "
                f"received camera_id={response_camera_id}"
            )

        image_id = response.get("image_id", response.get("id", "?"))
        print(
            f"Camera {camera_id}: stored {width}x{height} JPEG "
            f"-> CameraImage {image_id}; "
            f"quality={quality['quality_status']}; "
            f"vlm_ready={quality['vlm_ready']}."
        )
        return True

    def process_camera(self, camera: dict[str, Any], *, force: bool = False) -> bool:
        camera_id = camera.get("id", camera.get("camera_id"))
        if camera_id is None:
            print("Skipping camera without id.")
            return False

        latest = self.backend.get_latest_image(camera_id)
        now_local = datetime.now(self.zone)
        decision = capture_decision(
            camera,
            latest,
            now_local=now_local,
            timezone_name=self.timezone_name,
            force=force,
        )
        if not decision.due:
            next_due = decision.due_at.isoformat() if decision.due_at else "n/a"
            print(f"Camera {camera_id}: skip ({decision.reason}; next_due={next_due}).")
            return False

        due_at = decision.due_at.isoformat() if decision.due_at else "manual"
        print(f"Camera {camera_id}: capture ({decision.reason}; due_at={due_at}).")
        return self._upload_capture(camera, self._capture_and_encode(camera))

    def _process_due_batch(
        self,
        due: list[tuple[dict[str, Any], CaptureDecision]],
    ) -> int:
        """Capture and persist every Camera that is due in this poll."""
        captures: list[
            tuple[
                dict[str, Any],
                tuple[
                    bytes,
                    datetime,
                    int,
                    int,
                    dict[str, Any],
                ],
            ]
        ] = []

        for camera, decision in due:
            camera_id = camera.get("id", camera.get("camera_id", "?"))
            due_at = decision.due_at.isoformat() if decision.due_at else "now"
            print(f"Camera {camera_id}: due-batch capture (due_at={due_at}).")
            try:
                captures.append((camera, self._capture_and_encode(camera)))
            except Exception as exc:
                print(f"Camera {camera_id}: capture ERROR: {exc}")

        success_count = 0
        for camera, capture in captures:
            try:
                if self._upload_capture(camera, capture):
                    success_count += 1
            except Exception as exc:
                print(f"Camera {camera.get('id', '?')}: persistence ERROR: {exc}")
        return success_count

    def process_all(self, *, camera_id: int | None = None, force: bool = False) -> int:
        if camera_id is not None:
            try:
                return int(
                    self.process_camera(
                        self.backend.get_camera(camera_id),
                        force=force,
                    )
                )
            except Exception as exc:
                print(f"Camera {camera_id}: ERROR: {exc}")
                return 0

        cameras = self.backend.get_cameras()
        now_local = datetime.now(self.zone)
        due: list[tuple[dict[str, Any], CaptureDecision]] = []

        for camera in cameras:
            camera_id_value = camera.get("id", camera.get("camera_id"))
            if camera_id_value is None:
                print("Skipping camera without id.")
                continue

            try:
                latest = self.backend.get_latest_image(camera_id_value)
                decision = capture_decision(
                    camera,
                    latest,
                    now_local=now_local,
                    timezone_name=self.timezone_name,
                    force=force,
                )
            except Exception as exc:
                print(f"Camera {camera_id_value}: schedule ERROR: {exc}")
                continue

            if decision.due:
                due.append((camera, decision))
            else:
                next_due = decision.due_at.isoformat() if decision.due_at else "n/a"
                print(
                    f"Camera {camera_id_value}: skip "
                    f"({decision.reason}; next_due={next_due})."
                )

        if not due:
            return 0

        if len(due) > 1:
            ids = ", ".join(str(camera.get("id", "?")) for camera, _ in due)
            print(f"Capture batch due for Cameras: {ids}")

        return self._process_due_batch(due)
