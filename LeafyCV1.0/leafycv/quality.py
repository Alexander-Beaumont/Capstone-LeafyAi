"""Deterministic image-quality gate used before VLM visual input.

The goal is not to judge plant health.  The gate only checks whether the
camera image is technically suitable for reliable CV/VLM interpretation.
Thresholds are conservative MVP defaults and should be calibrated with farm
images if the final hardware changes.
"""

from __future__ import annotations

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# MVP quality thresholds
# ---------------------------------------------------------------------------
MIN_WIDTH = 320
MIN_HEIGHT = 240
MIN_BRIGHTNESS = 25.0
MAX_BRIGHTNESS = 235.0
MIN_BLUR_VARIANCE = 25.0
MAX_UNDEREXPOSED_PERCENTAGE = 70.0
MAX_OVEREXPOSED_PERCENTAGE = 70.0
MIN_CONTRAST_STD = 18.0
MAGENTA_PIXEL_PERCENTAGE_LIMIT = 30.0
MAGENTA_MEAN_EXCESS_LIMIT = 18.0


FLAG_DESCRIPTIONS = {
    "INVALID_ROI": "configured growth-area ROI is invalid",
    "LOW_RESOLUTION": "growth-area resolution is too low",
    "BLURRY": "image appears out of focus or motion blurred",
    "TOO_DARK": "image is too dark / underexposed",
    "TOO_BRIGHT": "image is too bright / overexposed",
    "LOW_CONTRAST": "image contrast is too low",
    "MAGENTA_CAST": "strong magenta lighting / colour cast is present",
}


def _quality_message(flags: list[str]) -> str:
    """Create a deterministic message that can be shown without using a VLM."""
    if not flags:
        return "Image quality passed LeafyCV checks and is suitable for VLM visual input."

    readable = [FLAG_DESCRIPTIONS.get(flag, flag.lower()) for flag in flags]
    reasons = "; ".join(readable)
    return (
        "Image rejected for visual AI because "
        f"{reasons}. Check camera lighting, focus, resolution, ROI, or viewing setup."
    )


def assess_image_quality(
    image: np.ndarray,
    *,
    roi_configured: bool = False,
    roi_valid: bool = True,
) -> dict:
    """Evaluate one full image or already-cropped growth area.

    Returned fields intentionally include both machine-routing values and debug
    metrics.  Backend persistence only needs the routing fields:

    - measurement_valid
    - vlm_ready
    - quality_status
    - quality_flags
    - quality_message

    Brightness/blur/etc. can remain LeafyCV debug information unless the team
    later decides to expose them on the dashboard.
    """
    if image is None or image.size == 0:
        flags = ["LOW_RESOLUTION"]
        if roi_configured and not roi_valid:
            flags.insert(0, "INVALID_ROI")
        return {
            "measurement_valid": False,
            "vlm_ready": False,
            "quality_status": "FAIL",
            "quality_flags": flags,
            "quality_message": _quality_message(flags),
            "roi_configured": bool(roi_configured),
            "roi_valid": bool(roi_valid),
            "width": 0,
            "height": 0,
            "brightness": 0.0,
            "blur_variance": 0.0,
            "contrast_std": 0.0,
            "underexposed_percentage": 100.0,
            "overexposed_percentage": 0.0,
            "magenta_pixel_percentage": 0.0,
            "magenta_mean_excess": 0.0,
        }

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Basic exposure/focus statistics.
    brightness = float(np.mean(gray))
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast_std = float(np.std(gray))
    under = float(np.mean(gray < 20) * 100.0)
    over = float(np.mean(gray > 245) * 100.0)

    # ------------------------------------------------------------------
    # Magenta cast detection
    # ------------------------------------------------------------------
    # Magenta typically means red and blue are both substantially stronger
    # than green.  We measure both the percentage of strongly magenta pixels
    # and the average positive magenta excess across the ROI.
    b, g, r = cv2.split(image.astype(np.float32))
    magenta_level = (r + b) / 2.0
    magenta_excess = magenta_level - g
    magenta_pixels = (r >= g + 20.0) & (b >= g + 20.0) & (magenta_level >= 80.0)
    magenta_pct = float(np.mean(magenta_pixels) * 100.0)
    magenta_mean_excess = float(np.mean(np.maximum(magenta_excess, 0.0)))

    flags: list[str] = []

    if roi_configured and not roi_valid:
        flags.append("INVALID_ROI")
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        flags.append("LOW_RESOLUTION")
    if blur_variance < MIN_BLUR_VARIANCE:
        flags.append("BLURRY")
    if brightness < MIN_BRIGHTNESS or under > MAX_UNDEREXPOSED_PERCENTAGE:
        flags.append("TOO_DARK")
    if brightness > MAX_BRIGHTNESS or over > MAX_OVEREXPOSED_PERCENTAGE:
        flags.append("TOO_BRIGHT")
    if contrast_std < MIN_CONTRAST_STD:
        flags.append("LOW_CONTRAST")
    if (
        magenta_pct >= MAGENTA_PIXEL_PERCENTAGE_LIMIT
        and magenta_mean_excess >= MAGENTA_MEAN_EXCESS_LIMIT
    ):
        flags.append("MAGENTA_CAST")

    passed = len(flags) == 0
    return {
        "measurement_valid": passed,
        "vlm_ready": passed,
        "quality_status": "PASS" if passed else "FAIL",
        "quality_flags": flags,
        "quality_message": _quality_message(flags),
        "roi_configured": bool(roi_configured),
        "roi_valid": bool(roi_valid),
        "width": int(width),
        "height": int(height),
        "brightness": round(brightness, 2),
        "blur_variance": round(blur_variance, 2),
        "contrast_std": round(contrast_std, 2),
        "underexposed_percentage": round(under, 2),
        "overexposed_percentage": round(over, 2),
        "magenta_pixel_percentage": round(magenta_pct, 2),
        "magenta_mean_excess": round(magenta_mean_excess, 2),
    }
