from __future__ import annotations

import cv2
import numpy as np


def assess_image_quality(image: np.ndarray) -> dict:
    """Return a lightweight quality gate for an analysis image."""
    if image is None or image.size == 0:
        return {
            "measurement_valid": False,
            "brightness": 0.0,
            "blur_variance": 0.0,
            "underexposed_percentage": 100.0,
            "overexposed_percentage": 0.0,
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    under = float(np.mean(gray < 20) * 100.0)
    over = float(np.mean(gray > 245) * 100.0)

    valid = (
        25.0 <= brightness <= 235.0
        and blur_variance >= 25.0
        and under <= 70.0
        and over <= 70.0
    )
    return {
        "measurement_valid": bool(valid),
        "brightness": round(brightness, 2),
        "blur_variance": round(blur_variance, 2),
        "underexposed_percentage": round(under, 2),
        "overexposed_percentage": round(over, 2),
    }
