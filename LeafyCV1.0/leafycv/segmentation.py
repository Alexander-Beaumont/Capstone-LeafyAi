from __future__ import annotations

import cv2
import numpy as np


def gray_world_balance(image: np.ndarray, gain_min: float = 0.60, gain_max: float = 2.20) -> np.ndarray:
    if image is None or image.size == 0:
        return image
    work = image.astype(np.float32)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    valid = (gray >= 15) & (gray <= 245)
    if np.count_nonzero(valid) < 100:
        valid = np.ones(gray.shape, dtype=bool)
    means = np.array([float(work[:, :, c][valid].mean()) for c in range(3)], dtype=np.float32)
    target = float(means.mean())
    gains = np.clip(target / (means + 1e-6), gain_min, gain_max)
    balanced = work * gains.reshape(1, 1, 3)
    return np.clip(balanced, 0, 255).astype(np.uint8)


def normalize_for_segmentation(image: np.ndarray) -> np.ndarray:
    balanced = gray_world_balance(image)
    lab = cv2.cvtColor(balanced, cv2.COLOR_BGR2LAB)
    lightness, channel_a, channel_b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lightness = clahe.apply(lightness)
    normalized = cv2.merge((lightness, channel_a, channel_b))
    return cv2.cvtColor(normalized, cv2.COLOR_LAB2BGR)


def _standard_masks(image: np.ndarray, cfg: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    h, saturation, value = cv2.split(hsv)
    _, channel_a, channel_b = cv2.split(lab)
    b, g, r = cv2.split(image)

    b16 = b.astype(np.int16)
    g16 = g.astype(np.int16)
    r16 = r.astype(np.int16)
    excess_green = 2 * g16 - r16 - b16

    exg_mask = np.where(excess_green >= int(cfg["exg_threshold"]), 255, 0).astype(np.uint8)
    dominant_green = np.where((g16 >= r16 + 6) & (g16 >= b16 + 6), 255, 0).astype(np.uint8)
    hsv_green = cv2.inRange(
        hsv,
        np.array([int(cfg["lower_h"]), int(cfg["min_s"]), int(cfg["min_v"])], dtype=np.uint8),
        np.array([int(cfg["upper_h"]), 255, 255], dtype=np.uint8),
    )
    green = cv2.bitwise_and(cv2.bitwise_and(hsv_green, exg_mask), dominant_green)

    yellow = np.where(
        (
            (h >= 10)
            & (h <= 45)
            & (saturation >= 30)
            & (value >= 75)
        )
        | (
            (channel_a >= 120)
            & (channel_a <= 170)
            & (channel_b >= 140)
            & (saturation >= 25)
            & (value >= 60)
        ),
        255,
        0,
    ).astype(np.uint8)
    yellow = cv2.bitwise_and(yellow, cv2.bitwise_not(green))

    brown = np.where(
        (
            (h >= 5)
            & (h <= 35)
            & (saturation >= 20)
            & (value >= 20)
            & (value <= 160)
            & (r16 >= g16)
        )
        | (
            (channel_a >= 145)
            & (channel_b >= 120)
            & (value >= 15)
            & (value <= 160)
        ),
        255,
        0,
    ).astype(np.uint8)
    brown = cv2.bitwise_and(brown, cv2.bitwise_not(green))
    brown = cv2.bitwise_and(brown, cv2.bitwise_not(yellow))
    return green, yellow, brown


def _remove_small_noise(mask: np.ndarray, minimum_pixels: int, minimum_ratio: float) -> np.ndarray:
    minimum_area = max(int(minimum_pixels), int(mask.size * float(minimum_ratio)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    cleaned = np.zeros_like(mask)
    for component_id in range(1, count):
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        if area >= minimum_area:
            cleaned[labels == component_id] = 255
    return cleaned


def segment_vegetation(image: np.ndarray, lighting_mode: str, segmentation_cfg: dict, analysis_cfg: dict) -> dict[str, np.ndarray]:
    """Return vegetation presence and colour masks for one ROI.

    Under MAGENTA lighting, the combined canopy mask remains available, but
    green/yellow percentages are not considered biologically reliable.
    """
    if image is None or image.size == 0:
        empty = np.zeros((1, 1), dtype=np.uint8)
        return {"combined": empty, "green": empty, "yellow": empty, "brown": empty}

    lighting_mode = str(lighting_mode).upper()
    normalized = normalize_for_segmentation(image)
    green, yellow, brown = _standard_masks(normalized, segmentation_cfg)

    presence = green.copy()
    if lighting_mode == "MAGENTA":
        hsv_original = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab_original = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        _, saturation, value = cv2.split(hsv_original)
        _, channel_a, channel_b = cv2.split(lab_original)
        magenta_leaf = np.where(
            (channel_a <= int(segmentation_cfg["lab_a_max"]) + 12)
            & (channel_b >= int(segmentation_cfg["lab_b_min"]) - 10)
            & (saturation >= max(35, int(int(segmentation_cfg["magenta_min_s"]) * 0.65)))
            & (value >= int(segmentation_cfg["min_v"]))
            & (value <= min(235, int(segmentation_cfg["magenta_max_v"]) + 20)),
            255,
            0,
        ).astype(np.uint8)
        presence = cv2.bitwise_or(presence, magenta_leaf)

    combined = cv2.bitwise_or(presence, yellow)
    combined = cv2.bitwise_or(combined, brown)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    combined = _remove_small_noise(
        combined,
        int(analysis_cfg["min_component_pixels"]),
        float(analysis_cfg["min_component_ratio"]),
    )

    green = cv2.bitwise_and(green, combined)
    yellow = cv2.bitwise_and(yellow, combined)
    brown = cv2.bitwise_and(brown, combined)
    return {"combined": combined, "green": green, "yellow": yellow, "brown": brown}
