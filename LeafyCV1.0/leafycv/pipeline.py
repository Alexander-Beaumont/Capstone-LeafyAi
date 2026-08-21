from __future__ import annotations

import time
from typing import Any

import cv2
import numpy as np

from .metrics import colour_percentages, crowding_index, growth_change, percentage
from .quality import assess_image_quality
from .segmentation import segment_growth_area


def _growth_area_rect(config: dict[str, Any] | None, width: int, height: int) -> tuple[int, int, int, int]:
    config = config or {}
    roi = config.get("roi_points") or config.get("growth_area") or config.get("roi")
    if not isinstance(roi, dict):
        return 0, 0, width, height

    try:
        x = float(roi.get("x", 0.0))
        y = float(roi.get("y", 0.0))
        w = float(roi.get("width", 1.0))
        h = float(roi.get("height", 1.0))
    except (TypeError, ValueError):
        return 0, 0, width, height

    x = min(max(x, 0.0), 1.0)
    y = min(max(y, 0.0), 1.0)
    w = min(max(w, 0.01), 1.0)
    h = min(max(h, 0.01), 1.0)
    x2 = min(1.0, x + w)
    y2 = min(1.0, y + h)

    px0 = min(width - 1, max(0, round(x * width)))
    py0 = min(height - 1, max(0, round(y * height)))
    px1 = min(width, max(px0 + 1, round(x2 * width)))
    py1 = min(height, max(py0 + 1, round(y2 * height)))
    return px0, py0, px1, py1


def analyse_image(
    image: np.ndarray,
    *,
    camera_config: dict[str, Any] | None = None,
    previous_canopy: float | None = None,
) -> dict[str, Any]:
    """Analyse one raw image as a single growth area.

    No camera acquisition, SLOT registration, per-plant tracking, calibration-stick
    conversion, growth-stage classification or magenta-light mode is performed.
    """
    started = time.perf_counter()
    if image is None or image.size == 0:
        raise ValueError("Image is empty or unreadable.")

    height, width = image.shape[:2]
    x0, y0, x1, y1 = _growth_area_rect(camera_config, width, height)
    roi = image[y0:y1, x0:x1].copy()
    quality = assess_image_quality(roi)
    masks = segment_growth_area(roi)

    canopy = percentage(masks["combined"])
    green, yellow, _brown = colour_percentages(masks)
    crowding = crowding_index(masks["combined"])
    change = growth_change(canopy, previous_canopy)
    processing_ms = int(round((time.perf_counter() - started) * 1000.0))

    analysis = {
        "total_canopy_coverage": round(canopy, 2),
        "growth_change": None if change is None else round(change, 2),
        "crowding_percentage": round(crowding, 2),
        "green_percentage": round(green, 2),
        "yellow_percentage": round(yellow, 2),
        "measurement_valid": bool(quality["measurement_valid"]),
        "processing_time_ms": processing_ms,
    }

    annotated = image.copy()
    cv2.rectangle(annotated, (x0, y0), (x1 - 1, y1 - 1), (255, 255, 255), 2)
    lines = [
        f"Canopy: {analysis['total_canopy_coverage']:.1f}%",
        f"Crowding: {analysis['crowding_percentage']:.1f}%",
        "Growth: N/A" if analysis["growth_change"] is None else f"Growth: {analysis['growth_change']:+.1f}%",
        f"Green/Yellow: {analysis['green_percentage']:.1f}/{analysis['yellow_percentage']:.1f}%",
        f"Valid: {analysis['measurement_valid']}",
    ]
    text_y = max(22, y0 + 22)
    for line in lines:
        cv2.putText(annotated, line, (max(5, x0 + 6), text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
        text_y += 22

    full_mask = np.zeros((height, width), dtype=np.uint8)
    full_mask[y0:y1, x0:x1] = masks["combined"]

    return {
        "analysis": analysis,
        "quality": quality,
        "growth_area_pixels": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
        "annotated": annotated,
        "mask": full_mask,
    }
