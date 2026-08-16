from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .api import CVApiClient
from .calibration import pixels_per_cm
from .camera import open_live_capture, read_live_frame
from .config import load_config, normalized_point_to_pixels, normalized_roi_to_pixels, save_config
from .gui import close_windows, select_calibration_stick, select_roi, select_slot_centres
from .pipeline import analyse_frame

MONITOR_WINDOW = "LeafyCV1.0 Monitor"


def _source_signature(config: dict) -> tuple:
    camera = config["camera"]
    source_type = str(camera.get("source_type", "")).upper()
    if source_type == "WEBCAM":
        return (source_type, int(camera.get("webcam_index", 0)))
    if source_type == "RTSP":
        rtsp = camera.get("rtsp") or {}
        return (source_type, rtsp.get("ip_address"), int(rtsp.get("port", 554)), str(rtsp.get("path") or ""))
    return (source_type, str(camera.get("file_path") or ""))


def _time_text(value: datetime | None) -> str:
    return "Not yet" if value is None else value.strftime("%H:%M:%S")


def _draw_last_result(display: np.ndarray, config: dict, result: dict | None) -> None:
    if not result:
        return
    height, width = display.shape[:2]
    x0, y0, rw, rh = normalized_roi_to_pixels(config.get("roi"), width, height)
    plants_by_id = {str(p["slot_id"]): p for p in result.get("plants", [])}

    for slot in config.get("slots") or []:
        plant = plants_by_id.get(str(slot["slot_id"]))
        gx, gy = normalized_point_to_pixels(slot["centre"], width, height)
        if not plant:
            continue
        colour = (80, 230, 50) if plant.get("visible") else (120, 120, 120)
        cv2.circle(display, (gx, gy), 7, colour, -1)
        bbox = plant.get("bbox") or [0, 0, 0, 0]
        bx, by, bw, bh = [int(v) for v in bbox]
        if bw > 0 and bh > 0:
            cv2.rectangle(display, (x0 + bx, y0 + by), (x0 + bx + bw, y0 + by + bh), (80, 190, 255), 2)
        if plant.get("width_cm") is not None and plant.get("height_cm") is not None:
            size_text = f"{plant['width_cm']:.1f}x{plant['height_cm']:.1f}cm"
        else:
            size_text = f"{int(round(plant.get('width_px', 0)))}x{int(round(plant.get('height_px', 0)))}px"
        label = (
            f"{plant.get('slot_label', slot.get('label', slot['slot_id']))} "
            f"canopy:{float(plant.get('canopy_coverage', 0)):.1f}% "
            f"{size_text} crowd:{float(plant.get('crowding_percentage', 0)):.0f}%"
        )
        cv2.putText(display, label, (gx + 9, gy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, colour, 1, cv2.LINE_AA)


def render_monitor_preview(
    frame: np.ndarray,
    config: dict,
    last_result: dict | None,
    last_analysis_at: datetime | None,
    next_analysis_at: datetime | None,
    message: str = "",
) -> np.ndarray:
    """Draw live preview + configuration + most recent saved CV result.

    No frame-by-frame CV is performed here. Numeric values come only from the
    latest scheduled/manual saved analysis.
    """
    display = frame.copy()
    height, width = display.shape[:2]
    x0, y0, rw, rh = normalized_roi_to_pixels(config.get("roi"), width, height)
    cv2.rectangle(display, (x0, y0), (x0 + rw, y0 + rh), (255, 180, 40), 2)

    stick = config.get("calibration_stick")
    if stick:
        start = normalized_point_to_pixels(stick["start"], width, height)
        end = normalized_point_to_pixels(stick["end"], width, height)
        cv2.line(display, start, end, (255, 200, 50), 3, cv2.LINE_AA)
        middle = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
        cv2.putText(display, f"{float(stick['length_cm']):g} cm", (middle[0] + 7, middle[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 200, 50), 2, cv2.LINE_AA)

    for slot in config.get("slots") or []:
        gx, gy = normalized_point_to_pixels(slot["centre"], width, height)
        cv2.circle(display, (gx, gy), 5, (80, 190, 255), -1)
        cv2.putText(display, str(slot.get("label") or slot["slot_id"]), (gx + 7, gy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (80, 190, 255), 1, cv2.LINE_AA)

    _draw_last_result(display, config, last_result)

    overlay = display.copy()
    panel_height = 112
    cv2.rectangle(overlay, (0, 0), (min(width, 1250), panel_height), (20, 35, 28), -1)
    cv2.addWeighted(overlay, 0.80, display, 0.20, 0, display)

    analysis = (last_result or {}).get("analysis") or {}
    cv2.putText(display, f"LeafyCV1.0 LIVE PREVIEW | {config['lighting_mode']}", (14, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(
        display,
        f"Last analysed: {_time_text(last_analysis_at)} | Next: {_time_text(next_analysis_at)} | "
        f"visible:{analysis.get('visible_plant_count', '-')} canopy:{analysis.get('total_canopy_coverage', '-')}",
        (14, 53),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.47,
        (230, 240, 235),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(display, "Displayed CV values are from the last saved analysis, not from every live frame.", (14, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (230, 240, 235), 1, cv2.LINE_AA)
    cv2.putText(display, "Q quit | SPACE pause | S sample now | R ROI | P slots | C stick | X clear | N normal | M magenta", (14, 99), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 240, 235), 1, cv2.LINE_AA)
    if message:
        cv2.putText(display, message[:110], (14, min(height - 12, panel_height + 24)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 220, 255), 1, cv2.LINE_AA)
    return display


def run_monitor(
    *,
    config_loader: Callable[[], dict],
    local_config_path: Path | None,
    output_root: Path,
    api_client: CVApiClient,
    api_send_images: str,
    interval_minutes: float,
    fps: float,
    duration_seconds: float,
    slot_ids: list[str] | None,
    reference_length_cm: float | None,
    analyse_immediately: bool = True,
    refresh_config_seconds: float = 2.0,
) -> int:
    """Show a live camera continuously while saving CV data only at the interval."""
    if interval_minutes <= 0:
        raise ValueError("The analysis interval must be greater than zero minutes.")
    if fps <= 0:
        raise ValueError("Preview FPS must be greater than zero.")

    config = config_loader()
    source_type = str(config["camera"]["source_type"]).upper()
    if source_type == "FILE":
        raise ValueError("monitor requires a WEBCAM or RTSP source. Use demo/run-once for FILE sources.")
    if source_type == "RTSP":
        if fps > 1.0:
            raise ValueError("Direct RTSP monitor preview is limited to 1 FPS.")
        if duration_seconds <= 0:
            duration_seconds = 120.0
            print("Direct RTSP monitor is a bounded test; using 120 seconds.")
        if duration_seconds > 600:
            raise ValueError("Direct RTSP monitor sessions are limited to 600 seconds.")
        print("For the final lab deployment, React live preview should come from the backend/shared camera service.")
        print("LeafyCV scheduled analysis should use run-loop so RTSP is opened, captured and released every 30 minutes.")

    capture = open_live_capture(config)
    current_signature = _source_signature(config)
    cv2.namedWindow(MONITOR_WINDOW, cv2.WINDOW_NORMAL)

    paused = False
    current_frame: np.ndarray | None = None
    last_result: dict | None = None
    last_analysis_at: datetime | None = None
    now_dt = datetime.now().astimezone()
    next_analysis_at = now_dt if analyse_immediately else now_dt + timedelta(minutes=interval_minutes)
    started = time.monotonic()
    last_config_refresh = 0.0
    period = 1.0 / max(0.2, float(fps))
    message = ""
    sample_requested = False

    try:
        for _ in range(3):
            current_frame = read_live_frame(capture)

        while True:
            cycle_started = time.monotonic()
            if not paused:
                current_frame = read_live_frame(capture)
            if current_frame is None:
                raise RuntimeError("No live camera frame is available.")

            if time.monotonic() - last_config_refresh >= max(0.5, refresh_config_seconds):
                updated = config_loader()
                updated_signature = _source_signature(updated)
                if updated_signature != current_signature:
                    capture.release()
                    capture = open_live_capture(updated)
                    for _ in range(3):
                        current_frame = read_live_frame(capture)
                    current_signature = updated_signature
                    message = "Camera source changed; live capture reopened."
                config = updated
                last_config_refresh = time.monotonic()

            now_dt = datetime.now().astimezone()
            due = now_dt >= next_analysis_at
            if (due or sample_requested) and config.get("slots"):
                try:
                    result, _files = analyse_frame(
                        frame=current_frame.copy(),
                        config=config,
                        output_root=output_root,
                        captured_at=now_dt,
                        api_client=api_client,
                        api_send_images=api_send_images,
                    )
                    last_result = result
                    last_analysis_at = now_dt
                    next_analysis_at = now_dt + timedelta(minutes=interval_minutes)
                    message = f"Saved CV sample at {now_dt.strftime('%H:%M:%S')}."
                except Exception as exc:
                    next_analysis_at = now_dt + timedelta(minutes=interval_minutes)
                    message = f"Analysis failed: {exc}"
                    print(message)
                sample_requested = False
            elif due and not config.get("slots"):
                next_analysis_at = now_dt + timedelta(minutes=interval_minutes)
                message = "Scheduled analysis skipped: no SLOT positions are registered."

            display = render_monitor_preview(
                current_frame,
                config,
                last_result,
                last_analysis_at,
                next_analysis_at,
                message,
            )
            if paused:
                cv2.putText(display, "PAUSED", (display.shape[1] - 115, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (80, 220, 255), 2, cv2.LINE_AA)
            cv2.imshow(MONITOR_WINDOW, display)
            key = cv2.waitKey(1) & 0xFF

            if key in (27, ord("q"), ord("Q")):
                break
            if key == ord(" "):
                paused = not paused
            elif key in (ord("s"), ord("S")):
                sample_requested = True
                message = "Manual saved analysis requested."
            elif key in (ord("n"), ord("N"), ord("m"), ord("M"), ord("r"), ord("R"), ord("p"), ord("P"), ord("c"), ord("C"), ord("x"), ord("X")):
                if local_config_path is None:
                    message = "Configuration is backend-driven. Edit ROI/SLOT/calibration/lighting in React."
                else:
                    local_cfg = load_config(local_config_path)
                    if key in (ord("n"), ord("N")):
                        local_cfg["lighting_mode"] = "NORMAL"
                        save_config(local_config_path, local_cfg)
                        message = "Lighting mode set to NORMAL."
                    elif key in (ord("m"), ord("M")):
                        local_cfg["lighting_mode"] = "MAGENTA"
                        save_config(local_config_path, local_cfg)
                        message = "Lighting mode set to MAGENTA."
                    elif key in (ord("r"), ord("R")):
                        roi = select_roi(current_frame, local_cfg.get("roi"))
                        if roi is not None:
                            local_cfg["roi"] = roi
                            save_config(local_config_path, local_cfg)
                            message = "ROI updated."
                        cv2.namedWindow(MONITOR_WINDOW, cv2.WINDOW_NORMAL)
                    elif key in (ord("p"), ord("P")):
                        ids = slot_ids or [str(slot["slot_id"]) for slot in local_cfg.get("slots") or []]
                        if not ids:
                            message = "No SLOT IDs available. Start monitor with --slot-count or --slot-ids."
                        else:
                            roi_pixels = normalized_roi_to_pixels(local_cfg.get("roi"), current_frame.shape[1], current_frame.shape[0])
                            slots = select_slot_centres(current_frame, ids, roi_pixels)
                            if slots is not None:
                                local_cfg["slots"] = slots
                                save_config(local_config_path, local_cfg)
                                message = f"Registered {len(slots)} SLOT positions."
                        cv2.namedWindow(MONITOR_WINDOW, cv2.WINDOW_NORMAL)
                    elif key in (ord("c"), ord("C")):
                        length = reference_length_cm
                        if length is None and local_cfg.get("calibration_stick"):
                            length = float(local_cfg["calibration_stick"]["length_cm"])
                        if not length:
                            message = "Calibration length is unknown. Start monitor with --reference-length-cm 20."
                        else:
                            stick = select_calibration_stick(current_frame, float(length))
                            if stick is not None:
                                local_cfg["calibration_stick"] = stick
                                save_config(local_config_path, local_cfg)
                                message = f"Calibration stick updated ({float(length):g} cm)."
                        cv2.namedWindow(MONITOR_WINDOW, cv2.WINDOW_NORMAL)
                    elif key in (ord("x"), ord("X")):
                        local_cfg["calibration_stick"] = None
                        save_config(local_config_path, local_cfg)
                        message = "Calibration stick removed; pixel measurements remain available."
                    config = load_config(local_config_path)

            if duration_seconds > 0 and (time.monotonic() - started) >= duration_seconds:
                print("Monitor duration reached; closing camera.")
                break

            elapsed = time.monotonic() - cycle_started
            if elapsed < period:
                time.sleep(period - elapsed)
        return 0
    finally:
        capture.release()
        close_windows()
