#!/usr/bin/env python3
"""Lenient image-quality checks for LeafyCV1.0.

These checks are intentionally conservative. They only reject frames that are
obviously unusable (extreme blur/darkness/overexposure). They are not plant
health classifiers.
"""
from __future__ import annotations

import cv2
import numpy as np


def evaluate_image_quality(
    image: np.ndarray,
    *,
    min_blur_score: float = 15.0,
    min_mean_brightness: float = 10.0,
    max_mean_brightness: float = 245.0,
) -> dict:
    if image is None or image.size == 0:
        return {
            "measurement_valid": False,
            "blur_score": 0.0,
            "mean_brightness": 0.0,
            "reason": "empty_image",
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_brightness = float(gray.mean())

    reasons = []
    if blur_score < float(min_blur_score):
        reasons.append("image_too_blurry")
    if mean_brightness < float(min_mean_brightness):
        reasons.append("image_too_dark")
    if mean_brightness > float(max_mean_brightness):
        reasons.append("image_overexposed")

    return {
        "measurement_valid": not reasons,
        "blur_score": round(blur_score, 3),
        "mean_brightness": round(mean_brightness, 3),
        "reason": ",".join(reasons) if reasons else None,
    }
