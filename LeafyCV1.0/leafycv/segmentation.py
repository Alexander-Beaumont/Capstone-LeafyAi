from __future__ import annotations

import cv2
import numpy as np


def gray_world_balance(image: np.ndarray) -> np.ndarray:
    work = image.astype(np.float32)
    means = np.array(
        [max(float(work[:, :, c].mean()), 1.0) for c in range(3)],
        dtype=np.float32,
    )
    target = float(means.mean())
    gains = np.clip(target / means, 0.65, 1.8)
    return np.clip(work * gains.reshape(1, 1, 3), 0, 255).astype(np.uint8)


def normalize_image(image: np.ndarray) -> np.ndarray:
    balanced = gray_world_balance(image)
    lab = cv2.cvtColor(balanced, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _remove_small_components(
    mask: np.ndarray,
    min_pixels: int = 120,
    min_ratio: float = 0.00025,
) -> np.ndarray:
    min_area = max(int(min_pixels), int(mask.size * min_ratio))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    cleaned = np.zeros_like(mask)
    for component_id in range(1, count):
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        if area >= min_area:
            cleaned[labels == component_id] = 255
    return cleaned


def segment_colour_indicators(image: np.ndarray) -> dict[str, np.ndarray]:
    """Produce normal/white-light green/yellow/brown candidate masks.

    These masks are NOT the canopy source of truth. The semantic U-Net canopy
    mask is applied later so colour percentages are calculated only inside
    pixels the model identified as canopy.
    """
    normalized = normalize_image(image)
    hsv = cv2.cvtColor(normalized, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(normalized, cv2.COLOR_BGR2LAB)
    h, s, v = cv2.split(hsv)
    _, a, b_lab = cv2.split(lab)
    bgr_b, bgr_g, bgr_r = cv2.split(normalized)

    b16 = bgr_b.astype(np.int16)
    g16 = bgr_g.astype(np.int16)
    r16 = bgr_r.astype(np.int16)
    exg = 2 * g16 - r16 - b16

    green_hsv = cv2.inRange(
        hsv,
        np.array([30, 35, 30], np.uint8),
        np.array([95, 255, 255], np.uint8),
    )
    green_dom = np.where((g16 >= r16 + 4) & (g16 >= b16 + 4), 255, 0).astype(np.uint8)
    exg_mask = np.where(exg >= 18, 255, 0).astype(np.uint8)
    green = cv2.bitwise_and(green_hsv, green_dom)
    green = cv2.bitwise_and(green, exg_mask)

    yellow = np.where(
        ((h >= 12) & (h <= 42) & (s >= 35) & (v >= 65))
        | ((a >= 118) & (a <= 165) & (b_lab >= 138) & (s >= 25) & (v >= 55)),
        255,
        0,
    ).astype(np.uint8)
    yellow = cv2.bitwise_and(yellow, cv2.bitwise_not(green))

    brown = np.where(
        ((h >= 4) & (h <= 32) & (s >= 25) & (v >= 25) & (v <= 170) & (r16 >= g16))
        | ((a >= 142) & (b_lab >= 120) & (v >= 20) & (v <= 170)),
        255,
        0,
    ).astype(np.uint8)
    brown = cv2.bitwise_and(brown, cv2.bitwise_not(green))
    brown = cv2.bitwise_and(brown, cv2.bitwise_not(yellow))

    green = _remove_small_components(green)
    yellow = _remove_small_components(yellow)
    brown = _remove_small_components(brown)
    return {"green": green, "yellow": yellow, "brown": brown}
