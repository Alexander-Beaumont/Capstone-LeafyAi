"""Deterministic technical image-quality gate before VLM visual input.

This module belongs to Camera, not to Computer Vision.  It does not judge plant
health and does not calculate canopy/growth metrics.  It only decides whether an
official Camera frame is technically suitable to be offered to the team-owned
VLM module.

The gate preserves the useful checks from the earlier LeafyCV quality module,
adds IR/monochrome detection, and treats strong magenta grow-light colour cast as
a warning rather than a failure.  The VLM teammate has validated that magenta
frames remain useful, so ``vlm_ready`` stays True when magenta is the only issue.
"""
from __future__ import annotations

from typing import Any

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# MVP quality thresholds
# ---------------------------------------------------------------------------
MIN_WIDTH = 320
MIN_HEIGHT = 240
MIN_BRIGHTNESS = 25.0
MAX_BRIGHTNESS = 235.0

# The earlier CV gate used 25.0.  VLM testing showed a useful magenta farm image
# at ~19 Laplacian variance, so the VLM-facing technical gate is deliberately
# slightly more tolerant while still rejecting strongly blurred frames.
MIN_BLUR_VARIANCE = 18.0

MAX_UNDEREXPOSED_PERCENTAGE = 70.0
MAX_OVEREXPOSED_PERCENTAGE = 70.0
MIN_CONTRAST_STD = 18.0

# Retained from the earlier quality gate.  These now produce WARN only.
MAGENTA_PIXEL_PERCENTAGE_LIMIT = 30.0
MAGENTA_MEAN_EXCESS_LIMIT = 18.0
MAGENTA_PIXEL_RED_BLUE_MARGIN = 20.0
MAGENTA_MIN_LEVEL = 80.0

# IR / monochrome detection. A night-mode IP-camera frame can have acceptable
# luminance/focus while containing essentially no normal colour information.
MIN_MEAN_SATURATION = 8.0
COLOR_PIXEL_SATURATION_THRESHOLD = 20
MIN_COLOR_PIXEL_PERCENTAGE = 2.0


FLAG_DESCRIPTIONS = {
    "LOW_RESOLUTION": "image resolution is too low",
    "BLURRY": "image appears out of focus or motion blurred",
    "TOO_DARK": "image is too dark / underexposed",
    "TOO_BRIGHT": "image is too bright / overexposed",
    "LOW_CONTRAST": "image contrast is too low",
    "MONOCHROME_OR_IR": "image appears monochrome/infrared and lacks normal colour information",
    "MAGENTA_CAST": "strong magenta lighting / colour cast is present",
}


def _quality_message(fail_flags: list[str], warning_flags: list[str]) -> str:
    """Create a deterministic message without calling a VLM."""
    if fail_flags:
        reasons = "; ".join(FLAG_DESCRIPTIONS.get(flag, flag.lower()) for flag in fail_flags)
        return (
            "Image rejected for VLM visual input because "
            f"{reasons}. Check camera exposure, focus, resolution, colour mode, or viewing setup."
        )

    if warning_flags:
        reasons = "; ".join(FLAG_DESCRIPTIONS.get(flag, flag.lower()) for flag in warning_flags)
        return (
            "Image passed the technical VLM gate with a quality warning: "
            f"{reasons}. VLM visual input remains allowed."
        )

    return "Image quality passed Camera checks and is suitable for VLM visual input."


def _empty_metrics() -> dict[str, float | int]:
    return {
        "width": 0,
        "height": 0,
        "brightness": 0.0,
        "blur_variance": 0.0,
        "contrast_std": 0.0,
        "underexposed_percentage": 100.0,
        "overexposed_percentage": 0.0,
        "mean_saturation": 0.0,
        "color_pixel_percentage": 0.0,
        "magenta_pixel_percentage": 0.0,
        "magenta_mean_excess": 0.0,
    }


def assess_image_quality(image: np.ndarray) -> dict[str, Any]:
    """Evaluate one official full-frame Camera image.

    Routing fields:
      - ``vlm_ready``
      - ``quality_status``: PASS / WARN / FAIL
      - ``quality_flags``
      - ``quality_message``

    ``quality_metrics`` retains deterministic technical measurements for Lab
    debugging.  Magenta may set ``MAGENTA_CAST`` + WARN but never blocks VLM.
    """
    if image is None or image.size == 0:
        fail_flags = ["LOW_RESOLUTION"]
        return {
            "vlm_ready": False,
            "quality_status": "FAIL",
            "quality_flags": fail_flags,
            "quality_message": _quality_message(fail_flags, []),
            "quality_metrics": _empty_metrics(),
        }

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]

    # Exposure / focus / contrast statistics retained from the earlier gate.
    brightness = float(np.mean(gray))
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast_std = float(np.std(gray))
    under = float(np.mean(gray < 20) * 100.0)
    over = float(np.mean(gray > 245) * 100.0)

    # Colour availability: catches infrared/night mode that luminance checks miss.
    mean_saturation = float(np.mean(saturation))
    color_pixel_percentage = float(
        np.mean(saturation >= COLOR_PIXEL_SATURATION_THRESHOLD) * 100.0
    )

    # Magenta diagnostics retained from the previous quality implementation.
    b, g, r = cv2.split(image.astype(np.float32))
    magenta_level = (r + b) / 2.0
    magenta_excess = magenta_level - g
    magenta_pixels = (
        (r >= g + MAGENTA_PIXEL_RED_BLUE_MARGIN)
        & (b >= g + MAGENTA_PIXEL_RED_BLUE_MARGIN)
        & (magenta_level >= MAGENTA_MIN_LEVEL)
    )
    magenta_pct = float(np.mean(magenta_pixels) * 100.0)
    magenta_mean_excess = float(np.mean(np.maximum(magenta_excess, 0.0)))

    fail_flags: list[str] = []
    warning_flags: list[str] = []

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        fail_flags.append("LOW_RESOLUTION")
    if blur_variance < MIN_BLUR_VARIANCE:
        fail_flags.append("BLURRY")
    if brightness < MIN_BRIGHTNESS or under > MAX_UNDEREXPOSED_PERCENTAGE:
        fail_flags.append("TOO_DARK")
    if brightness > MAX_BRIGHTNESS or over > MAX_OVEREXPOSED_PERCENTAGE:
        fail_flags.append("TOO_BRIGHT")
    if contrast_std < MIN_CONTRAST_STD:
        fail_flags.append("LOW_CONTRAST")
    if (
        mean_saturation < MIN_MEAN_SATURATION
        and color_pixel_percentage < MIN_COLOR_PIXEL_PERCENTAGE
    ):
        fail_flags.append("MONOCHROME_OR_IR")

    if (
        magenta_pct >= MAGENTA_PIXEL_PERCENTAGE_LIMIT
        and magenta_mean_excess >= MAGENTA_MEAN_EXCESS_LIMIT
    ):
        warning_flags.append("MAGENTA_CAST")

    if fail_flags:
        status = "FAIL"
        vlm_ready = False
    elif warning_flags:
        status = "WARN"
        vlm_ready = True
    else:
        status = "PASS"
        vlm_ready = True

    all_flags = fail_flags + warning_flags
    return {
        "vlm_ready": vlm_ready,
        "quality_status": status,
        "quality_flags": all_flags,
        "quality_message": _quality_message(fail_flags, warning_flags),
        "quality_metrics": {
            "width": int(width),
            "height": int(height),
            "brightness": round(brightness, 2),
            "blur_variance": round(blur_variance, 2),
            "contrast_std": round(contrast_std, 2),
            "underexposed_percentage": round(under, 2),
            "overexposed_percentage": round(over, 2),
            "mean_saturation": round(mean_saturation, 2),
            "color_pixel_percentage": round(color_pixel_percentage, 2),
            "magenta_pixel_percentage": round(magenta_pct, 2),
            "magenta_mean_excess": round(magenta_mean_excess, 2),
        },
    }
