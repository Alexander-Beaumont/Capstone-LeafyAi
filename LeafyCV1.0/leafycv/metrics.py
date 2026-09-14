from __future__ import annotations

import numpy as np


def percentage(mask: np.ndarray) -> float:
    if mask is None or mask.size == 0:
        return 0.0
    return float(np.count_nonzero(mask) / mask.size * 100.0)


def colour_percentages(masks: dict[str, np.ndarray]) -> tuple[float, float, float]:
    """Colour percentages using semantic canopy pixels as the denominator."""
    canopy_pixels = int(np.count_nonzero(masks["combined"]))
    if canopy_pixels <= 0:
        return 0.0, 0.0, 0.0
    green = np.count_nonzero(masks["green"]) / canopy_pixels * 100.0
    yellow = np.count_nonzero(masks["yellow"]) / canopy_pixels * 100.0
    brown = np.count_nonzero(masks["brown"]) / canopy_pixels * 100.0
    return float(green), float(yellow), float(brown)


def crowding_index(
    mask: np.ndarray,
    rows: int = 4,
    cols: int = 6,
    dense_threshold: float = 0.70,
) -> float:
    """Percentage of growth-area grid cells densely occupied by canopy."""
    h, w = mask.shape[:2]
    dense = 0
    total = 0
    for r in range(rows):
        y0 = round(r * h / rows)
        y1 = round((r + 1) * h / rows)
        for c in range(cols):
            x0 = round(c * w / cols)
            x1 = round((c + 1) * w / cols)
            cell = mask[y0:y1, x0:x1]
            if cell.size == 0:
                continue
            total += 1
            occupancy = np.count_nonzero(cell) / cell.size
            if occupancy >= dense_threshold:
                dense += 1
    return 0.0 if total == 0 else float(dense / total * 100.0)


def growth_change(current_canopy: float, previous_canopy: float | None) -> float | None:
    """Relative canopy change percentage against the previous valid analysis."""
    if previous_canopy is None or previous_canopy <= 0.1:
        return None
    return float((current_canopy - previous_canopy) / previous_canopy * 100.0)
