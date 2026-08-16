from __future__ import annotations

import math
from typing import Any

from .config import normalized_point_to_pixels


def pixels_per_cm(config: dict[str, Any], frame_width: int, frame_height: int) -> float | None:
    stick = config.get("calibration_stick")
    if not stick:
        return None
    start = normalized_point_to_pixels(stick["start"], frame_width, frame_height)
    end = normalized_point_to_pixels(stick["end"], frame_width, frame_height)
    pixel_length = math.dist(start, end)
    real_length_cm = float(stick["length_cm"])
    if pixel_length <= 1.0 or real_length_cm <= 0:
        return None
    return pixel_length / real_length_cm
