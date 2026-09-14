"""LeafyCV1.0 end-to-end analysis pipeline for one official CameraImage."""

from __future__ import annotations

import time
from typing import Any, Protocol

import cv2
import numpy as np

from .metrics import colour_percentages, crowding_index, growth_change, percentage
from .quality import assess_image_quality
from .segmentation import segment_colour_indicators
from .semantic_segmenter import get_default_segmenter


class Segmenter(Protocol):
    """Minimal interface used by the pipeline and easy to mock in unit tests."""

    def segment(self, image_bgr: np.ndarray) -> dict[str, Any]: ...


def _resolve_growth_area(
    config: dict[str, Any] | None,
    width: int,
    height: int,
) -> tuple[tuple[int, int, int, int], bool, bool]:
    """Resolve the final normalized rectangle ROI contract.

    Final format stored on one Camera record:

        {
            "x": 0.10,
            "y": 0.12,
            "width": 0.80,
            "height": 0.72
        }

    Values are normalized to 0..1 so the same ROI works on a small React
    preview and the original RTSP image.  Missing ROI intentionally means
    whole-frame analysis.  A malformed configured ROI falls back to the whole
    frame for debug output but is marked invalid by the quality gate.
    """
    config = config or {}
    roi = config.get("roi_points") or config.get("growth_area") or config.get("roi")

    if roi in (None, ""):
        return (0, 0, width, height), False, True
    if not isinstance(roi, dict):
        return (0, 0, width, height), True, False

    try:
        x = float(roi["x"])
        y = float(roi["y"])
        w = float(roi["width"])
        h = float(roi["height"])
    except (KeyError, TypeError, ValueError):
        return (0, 0, width, height), True, False

    valid = (
        0.0 <= x < 1.0
        and 0.0 <= y < 1.0
        and 0.0 < w <= 1.0
        and 0.0 < h <= 1.0
        and x + w <= 1.0 + 1e-9
        and y + h <= 1.0 + 1e-9
    )
    if not valid:
        return (0, 0, width, height), True, False

    x0 = max(0, min(width - 1, round(x * width)))
    y0 = max(0, min(height - 1, round(y * height)))
    x1 = max(x0 + 1, min(width, round((x + w) * width)))
    y1 = max(y0 + 1, min(height, round((y + h) * height)))
    return (x0, y0, x1, y1), True, True


def analyse_image(
    image: np.ndarray,
    *,
    camera_config: dict[str, Any] | None = None,
    previous_canopy: float | None = None,
    segmenter: Segmenter | None = None,
) -> dict[str, Any]:
    """Analyse one official image as one camera-level growth area.

    Processing order:

    1. Resolve the Camera-specific ROI.
    2. Run deterministic image-quality checks on that growth area.
    3. Run U-Net + EfficientNet-B0 semantic canopy segmentation.
    4. Restrict OpenCV colour indicators to semantic canopy pixels.
    5. Calculate canopy/crowding/colour metrics.
    6. Calculate growth_change only when the current measurement is valid.
    7. Return aggregate JSON fields plus local debug images.

    A quality FAIL does not crash analysis.  Metrics are still available for
    debugging, but measurement_valid=False and vlm_ready=False tell downstream
    systems not to trust the image for growth baselines or VLM visual analysis.
    """
    started = time.perf_counter()
    if image is None or image.size == 0:
        raise ValueError("Image is empty or unreadable.")

    # ------------------------------------------------------------------
    # Camera-specific Growth Area ROI
    # ------------------------------------------------------------------
    height, width = image.shape[:2]
    (x0, y0, x1, y1), roi_configured, roi_valid = _resolve_growth_area(
        camera_config,
        width,
        height,
    )
    roi = image[y0:y1, x0:x1].copy()

    # ------------------------------------------------------------------
    # Quality gate before the image is considered safe for VLM usage
    # ------------------------------------------------------------------
    quality = assess_image_quality(
        roi,
        roi_configured=roi_configured,
        roi_valid=roi_valid,
    )

    # ------------------------------------------------------------------
    # Semantic canopy segmentation - source of truth for plant pixels
    # ------------------------------------------------------------------
    semantic = (segmenter or get_default_segmenter()).segment(roi)
    canopy_mask = np.asarray(semantic["mask"], dtype=np.uint8)
    if canopy_mask.shape[:2] != roi.shape[:2]:
        raise ValueError("Semantic segmenter returned a mask with the wrong size.")

    # ------------------------------------------------------------------
    # Colour indicators remain OpenCV-based, but are restricted to pixels
    # already classified as canopy by the semantic model.
    # ------------------------------------------------------------------
    colour_candidates = segment_colour_indicators(roi)
    green = cv2.bitwise_and(colour_candidates["green"], canopy_mask)
    yellow = cv2.bitwise_and(colour_candidates["yellow"], canopy_mask)
    brown = cv2.bitwise_and(colour_candidates["brown"], canopy_mask)
    masks = {
        "combined": canopy_mask,
        "green": green,
        "yellow": yellow,
        "brown": brown,
    }

    # ------------------------------------------------------------------
    # Aggregate Growth Area metrics
    # ------------------------------------------------------------------
    canopy = percentage(canopy_mask)
    green_pct, yellow_pct, _brown_pct = colour_percentages(masks)
    crowding = crowding_index(canopy_mask)

    # Invalid current images must not create a misleading growth comparison.
    change = (
        growth_change(canopy, previous_canopy)
        if quality["measurement_valid"]
        else None
    )

    processing_ms = int(round((time.perf_counter() - started) * 1000.0))

    # These names are the final Backend/Frontend/AI Agent contract.  Do not
    # rename them independently in LeafyCV, Django serializers, or React.
    analysis = {
        "total_canopy_coverage": round(canopy, 2),
        "growth_change": None if change is None else round(change, 2),
        "crowding_percentage": round(crowding, 2),
        "green_percentage": round(green_pct, 2),
        "yellow_percentage": round(yellow_pct, 2),
        "measurement_valid": bool(quality["measurement_valid"]),
        "vlm_ready": bool(quality["vlm_ready"]),
        "quality_status": str(quality["quality_status"]),
        "quality_flags": list(quality["quality_flags"]),
        "quality_message": str(quality["quality_message"]),
        "processing_time_ms": processing_ms,
    }

    # ------------------------------------------------------------------
    # Local debug annotation.  These images are not part of the Backend
    # production contract and do not need to be stored in the database.
    # ------------------------------------------------------------------
    annotated = image.copy()
    cv2.rectangle(annotated, (x0, y0), (x1 - 1, y1 - 1), (255, 255, 255), 2)
    lines = [
        f"Canopy: {analysis['total_canopy_coverage']:.1f}%",
        f"Crowding: {analysis['crowding_percentage']:.1f}%",
        "Growth: N/A"
        if analysis["growth_change"] is None
        else f"Growth: {analysis['growth_change']:+.1f}%",
        f"Green/Yellow: {analysis['green_percentage']:.1f}/{analysis['yellow_percentage']:.1f}%",
        f"Quality: {analysis['quality_status']} | VLM: {analysis['vlm_ready']}",
    ]

    text_y = max(22, y0 + 22)
    for line in lines:
        cv2.putText(
            annotated,
            line,
            (max(5, x0 + 6), text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        text_y += 22

    # Restore ROI-only semantic outputs to full-frame debug canvases.
    full_mask = np.zeros((height, width), dtype=np.uint8)
    full_mask[y0:y1, x0:x1] = canopy_mask

    probability_roi = semantic.get("probability")
    full_probability: np.ndarray | None = None
    if isinstance(probability_roi, np.ndarray):
        full_probability = np.zeros((height, width), dtype=np.float32)
        full_probability[y0:y1, x0:x1] = probability_roi.astype(np.float32)

    return {
        "analysis": analysis,
        "quality": quality,
        "growth_area_pixels": {
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "roi_configured": roi_configured,
            "roi_valid": roi_valid,
        },
        "annotated": annotated,
        "mask": full_mask,
        "probability": full_probability,
        "model": {
            "threshold": semantic.get("threshold"),
            "device": semantic.get("device"),
        },
    }
