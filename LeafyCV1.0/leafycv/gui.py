from __future__ import annotations

from typing import Sequence

import cv2
import numpy as np

from .config import pixel_point_to_normalized, pixel_roi_to_normalized

WINDOW = "LeafyCV1.0 Calibration"


def select_roi(frame: np.ndarray, existing_roi: dict | None = None) -> dict | None:
    display = frame.copy()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    print("ROI: drag a rectangle around the basil growing area, then press ENTER or SPACE.")
    print("ROI: press C or ESC to cancel and keep the current ROI.")
    roi = cv2.selectROI(WINDOW, display, showCrosshair=True, fromCenter=False)
    x, y, w, h = [int(v) for v in roi]
    if w <= 0 or h <= 0:
        return existing_roi
    return pixel_roi_to_normalized((x, y, w, h), frame.shape[1], frame.shape[0])


def select_slot_centres(
    frame: np.ndarray,
    slot_ids: Sequence[str],
    roi_pixels: tuple[int, int, int, int],
) -> list[dict] | None:
    points: list[tuple[int, int]] = []
    x0, y0, rw, rh = roi_pixels

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) >= len(slot_ids):
                return
            if x0 <= x <= x0 + rw and y0 <= y <= y0 + rh:
                points.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN and points:
            points.pop()

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, on_mouse)
    try:
        while True:
            display = frame.copy()
            cv2.rectangle(display, (x0, y0), (x0 + rw, y0 + rh), (255, 180, 40), 2)
            overlay = display.copy()
            cv2.rectangle(overlay, (0, 0), (min(display.shape[1], 980), 110), (20, 35, 28), -1)
            cv2.addWeighted(overlay, 0.80, display, 0.20, 0, display)
            next_label = str(slot_ids[len(points)]) if len(points) < len(slot_ids) else "complete"
            cv2.putText(display, "Register slot centres in the requested order", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(display, f"Left click add | Right click undo | ENTER finish | ESC cancel | Next: {next_label}", (15, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 240, 235), 1, cv2.LINE_AA)
            cv2.putText(display, f"Registered: {len(points)}/{len(slot_ids)}", (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (80, 220, 255), 1, cv2.LINE_AA)
            for index, (px, py) in enumerate(points):
                label = str(slot_ids[index])
                cv2.circle(display, (px, py), 7, (80, 190, 255), -1)
                cv2.putText(display, label, (px + 9, py - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (80, 190, 255), 2, cv2.LINE_AA)
            cv2.imshow(WINDOW, display)
            key = cv2.waitKey(20) & 0xFF
            if key == 27:
                return None
            if key in (13, ord(" ")):
                if len(points) != len(slot_ids):
                    print(f"Please register all {len(slot_ids)} slots before finishing.")
                    continue
                break
        return [
            {
                "slot_id": slot_id,
                "label": f"P{index + 1:02d}",
                "centre": pixel_point_to_normalized(point, frame.shape[1], frame.shape[0]),
            }
            for index, (slot_id, point) in enumerate(zip(slot_ids, points))
        ]
    finally:
        cv2.setMouseCallback(WINDOW, lambda *args: None)


def select_calibration_stick(frame: np.ndarray, length_cm: float) -> dict | None:
    points: list[tuple[int, int]] = []

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 2:
                points.append((x, y))
            else:
                points[:] = [(x, y)]
        elif event == cv2.EVENT_RBUTTONDOWN and points:
            points.pop()

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, on_mouse)
    try:
        while True:
            display = frame.copy()
            overlay = display.copy()
            cv2.rectangle(overlay, (0, 0), (min(display.shape[1], 980), 95), (20, 35, 28), -1)
            cv2.addWeighted(overlay, 0.80, display, 0.20, 0, display)
            cv2.putText(display, f"Calibration stick: select both ends of the {length_cm:g} cm reference", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(display, "Left click points | Right click undo | ENTER save | ESC cancel", (15, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 240, 235), 1, cv2.LINE_AA)
            for point in points:
                cv2.circle(display, point, 7, (255, 200, 50), -1)
            if len(points) == 2:
                cv2.line(display, points[0], points[1], (255, 200, 50), 3, cv2.LINE_AA)
                middle = ((points[0][0] + points[1][0]) // 2, (points[0][1] + points[1][1]) // 2)
                cv2.putText(display, f"{length_cm:g} cm", (middle[0] + 8, middle[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 50), 2, cv2.LINE_AA)
            cv2.imshow(WINDOW, display)
            key = cv2.waitKey(20) & 0xFF
            if key == 27:
                return None
            if key in (13, ord(" ")):
                if len(points) != 2:
                    print("Please select exactly two calibration-stick endpoints.")
                    continue
                return {
                    "start": pixel_point_to_normalized(points[0], frame.shape[1], frame.shape[0]),
                    "end": pixel_point_to_normalized(points[1], frame.shape[1], frame.shape[0]),
                    "length_cm": float(length_cm),
                }
    finally:
        cv2.setMouseCallback(WINDOW, lambda *args: None)


def close_windows() -> None:
    cv2.destroyAllWindows()
