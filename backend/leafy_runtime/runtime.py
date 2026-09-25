"""Background runtime services for Leafy AI."""

from __future__ import annotations

import os
import threading
import time

from django.db import close_old_connections

from camera_capture.config import SETTINGS as CAMERA_SETTINGS
from camera_capture.services import capture_due_once
from ai_agent.scheduler import run_due_schedules
from sensor_ingest.services.runtime import collect_due_configurations


_started = False
_start_lock = threading.Lock()


def _sensor_worker():
    """Poll runtime-editable per-device ingestion configurations."""

    # Give Django a moment to finish starting.
    time.sleep(2)

    print("Leafy AI sensor worker starting.")

    while True:
        close_old_connections()
        try:
            collect_due_configurations()
        except Exception as exc:
            print(f"Leafy AI sensor worker error: {exc}")
        finally:
            close_old_connections()
        # A short scheduler tick lets PATCHed poll intervals take effect without
        # restarting Django. Each device's own interval is enforced in the DB.
        time.sleep(1)


def _camera_worker():
    """
    Periodically ask camera_capture whether any configured Camera is due.

    capture_due_once() handles scheduling, archived Cameras, active hours,
    capture intervals, RTSP capture, quality checks, and CameraImage persistence.
    """

    interval = max(
        1.0,
        float(CAMERA_SETTINGS.poll_seconds),
    )

    # Give Django a moment to finish starting.
    time.sleep(2)

    print(
        "Leafy AI camera worker started "
        f"(check interval: {interval}s)."
    )

    while True:
        close_old_connections()

        try:
            captured = capture_due_once()

            if captured:
                print(
                    "Leafy AI camera worker: "
                    f"captured {captured} image(s)."
                )

        except Exception as exc:
            # A Camera/network failure must not terminate Django.
            print(
                "Leafy AI camera worker error: "
                f"{exc}"
            )

        finally:
            close_old_connections()

        time.sleep(interval)


def _ai_worker():
    """Poll per-farm recommendation schedules without terminating the runtime."""
    interval = max(5.0, float(os.getenv("LEAFY_AI_POLL_SECONDS", "30")))
    time.sleep(2)
    print(f"Leafy AI recommendation worker started (check interval: {interval}s).")
    while True:
        close_old_connections()
        try:
            run_due_schedules()
        except Exception as exc:
            print(f"Leafy AI recommendation worker error: {exc}")
        finally:
            close_old_connections()
        time.sleep(interval)


def start_background_runtime():
    """
    Start Leafy AI background services once in the current Django process.
    """

    global _started

    with _start_lock:
        if _started:
            return

        _started = True

        sensor_thread = threading.Thread(
            target=_sensor_worker,
            name="leafyai-sensor-worker",
            daemon=True,
        )

        camera_thread = threading.Thread(
            target=_camera_worker,
            name="leafyai-camera-worker",
            daemon=True,
        )

        ai_thread = threading.Thread(
            target=_ai_worker,
            name="leafyai-ai-worker",
            daemon=True,
        )

        sensor_thread.start()
        camera_thread.start()
        if os.getenv("LEAFY_AI_SCHEDULER_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}:
            ai_thread.start()

        print(
            "Leafy AI background runtime started "
            "(sensor ingestion + camera capture + AI scheduling)."
        )
