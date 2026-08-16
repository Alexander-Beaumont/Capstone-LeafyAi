from __future__ import annotations

import cv2
import numpy as np


def build_slot_map(width: int, height: int, centres_local: list[tuple[int, int]]) -> np.ndarray:
    if not centres_local:
        raise ValueError("At least one registered slot centre is required.")
    yy, xx = np.indices((height, width), dtype=np.float32)
    labels = np.zeros((height, width), dtype=np.int16)
    minimum_distance = np.full((height, width), np.inf, dtype=np.float32)
    for plant_index, (cx, cy) in enumerate(centres_local):
        distance = (xx - float(cx)) ** 2 + (yy - float(cy)) ** 2
        update = distance < minimum_distance
        labels[update] = plant_index
        minimum_distance[update] = distance[update]
    return labels


def slot_boundary_mask(slot_map: np.ndarray) -> np.ndarray:
    boundary = np.zeros(slot_map.shape, dtype=np.uint8)
    boundary[:, 1:] |= (slot_map[:, 1:] != slot_map[:, :-1]).astype(np.uint8) * 255
    boundary[1:, :] |= (slot_map[1:, :] != slot_map[:-1, :]).astype(np.uint8) * 255
    return boundary


def nearest_neighbour_radii(centres_local: list[tuple[int, int]], default_radius: int = 35) -> list[int]:
    if len(centres_local) <= 1:
        return [default_radius] * len(centres_local)
    radii: list[int] = []
    for i, (x1, y1) in enumerate(centres_local):
        nearest = min(
            ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            for j, (x2, y2) in enumerate(centres_local)
            if i != j
        )
        radii.append(int(max(12, min(60, nearest * 0.22))))
    return radii


def _robust_bbox(binary: np.ndarray, percentile: float = 2.5) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(binary)
    if xs.size < 20:
        return None
    trim = float(np.clip(percentile, 0.0, 15.0))
    if xs.size >= 100 and trim > 0:
        x1 = int(np.floor(np.percentile(xs, trim)))
        x2 = int(np.ceil(np.percentile(xs, 100.0 - trim)))
        y1 = int(np.floor(np.percentile(ys, trim)))
        y2 = int(np.ceil(np.percentile(ys, 100.0 - trim)))
    else:
        x1, x2 = int(xs.min()), int(xs.max())
        y1, y2 = int(ys.min()), int(ys.max())
    return x1, y1, max(1, x2 - x1 + 1), max(1, y2 - y1 + 1)


def measure_slots(
    *,
    masks: dict[str, np.ndarray],
    slot_map: np.ndarray,
    centres_local: list[tuple[int, int]],
    slots: list[dict],
    lighting_mode: str,
    analysis_cfg: dict,
    pixels_per_cm: float | None,
) -> list[dict]:
    combined = masks["combined"]
    green_mask = masks["green"]
    yellow_mask = masks["yellow"]
    brown_mask = masks["brown"]
    core_radii = nearest_neighbour_radii(centres_local)
    colour_valid = str(lighting_mode).upper() == "NORMAL"

    yy, xx = np.ogrid[:combined.shape[0], :combined.shape[1]]
    results: list[dict] = []

    for index, (slot_cfg, centre) in enumerate(zip(slots, centres_local)):
        slot_pixels = slot_map == index
        tissue = (combined > 0) & slot_pixels
        slot_area = int(np.count_nonzero(slot_pixels))
        canopy_area_px = int(np.count_nonzero(tissue))
        coverage = 100.0 * canopy_area_px / slot_area if slot_area else 0.0

        cx, cy = centre
        core = ((xx - cx) ** 2 + (yy - cy) ** 2 <= core_radii[index] ** 2) & slot_pixels
        core_area = int(np.count_nonzero(core))
        core_tissue = int(np.count_nonzero(tissue & core))
        core_ratio = core_tissue / core_area if core_area else 0.0
        visible = bool(
            core_ratio >= float(analysis_cfg["visible_core_threshold"])
            or coverage >= float(analysis_cfg["visible_area_threshold"])
        )

        bbox = _robust_bbox(tissue)
        if bbox is None:
            x = y = width_px = height_px = 0
        else:
            x, y, width_px, height_px = bbox

        width_cm = float(width_px) / pixels_per_cm if pixels_per_cm and width_px else None
        height_cm = float(height_px) / pixels_per_cm if pixels_per_cm and height_px else None

        green_percentage = yellow_percentage = brown_percentage = None
        if colour_valid:
            green_area = int(np.count_nonzero((green_mask > 0) & slot_pixels))
            yellow_area = int(np.count_nonzero((yellow_mask > 0) & slot_pixels))
            brown_area = int(np.count_nonzero((brown_mask > 0) & slot_pixels))
            colour_area = green_area + yellow_area + brown_area
            if colour_area > 0:
                green_percentage = 100.0 * green_area / colour_area
                yellow_percentage = 100.0 * yellow_area / colour_area
                brown_percentage = 100.0 * brown_area / colour_area
            else:
                green_percentage = yellow_percentage = brown_percentage = 0.0

        results.append(
            {
                "slot_id": slot_cfg["slot_id"],
                "slot_label": slot_cfg.get("label") or str(slot_cfg["slot_id"]),
                "centre_local": [int(cx), int(cy)],
                "canopy_area_px": canopy_area_px,
                "canopy_coverage": float(coverage),
                "bbox": [int(x), int(y), int(width_px), int(height_px)],
                "width_px": float(width_px),
                "height_px": float(height_px),
                "width_cm": width_cm,
                "height_cm": height_cm,
                "green_percentage": green_percentage,
                "yellow_percentage": yellow_percentage,
                "brown_percentage": brown_percentage,
                "colour_measurement_valid": colour_valid,
                "core_tissue_ratio": float(core_ratio),
                "visible": visible,
                "measurement_valid": visible,
            }
        )
    return results
