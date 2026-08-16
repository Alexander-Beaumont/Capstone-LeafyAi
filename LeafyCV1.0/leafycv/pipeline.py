from __future__ import annotations

import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from . import MODEL_VERSION
from .api import CVApiClient, build_backend_payload
from .calibration import pixels_per_cm
from .camera import capture_frame
from .config import normalized_point_to_pixels, normalized_roi_to_pixels
from .crowding import compute_crowding
from .outputs import save_sample, slugify
from .quality import evaluate_image_quality
from .segmentation import segment_vegetation
from .slots import build_slot_map, measure_slots, slot_boundary_mask
from .state import apply_growth_and_temporal_checks, load_state, save_state


def _slot_centres_local(config: dict, frame_width: int, frame_height: int, roi: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    x0, y0, rw, rh = roi
    centres: list[tuple[int, int]] = []
    for slot in config["slots"]:
        gx, gy = normalized_point_to_pixels(slot["centre"], frame_width, frame_height)
        lx, ly = gx - x0, gy - y0
        if not (0 <= lx < rw and 0 <= ly < rh):
            raise ValueError(
                f"Registered slot {slot['slot_id']} is outside the configured ROI. "
                "Adjust the ROI or re-register the slot centre."
            )
        centres.append((lx, ly))
    return centres


def _draw_annotation(
    *,
    frame: np.ndarray,
    roi: tuple[int, int, int, int],
    slot_map: np.ndarray,
    centres_local: list[tuple[int, int]],
    plants: list[dict],
    config: dict,
    ppcm: float | None,
    total_canopy: float,
    image_valid: bool,
) -> np.ndarray:
    annotated = frame.copy()
    x0, y0, rw, rh = roi
    cv2.rectangle(annotated, (x0, y0), (x0 + rw, y0 + rh), (255, 180, 40), 2)

    boundary = slot_boundary_mask(slot_map)
    yy, xx = np.where(boundary > 0)
    annotated[y0 + yy, x0 + xx] = (170, 90, 220)

    for index, (centre, plant) in enumerate(zip(centres_local, plants)):
        cx, cy = centre
        gx, gy = x0 + cx, y0 + cy
        marker_colour = (80, 230, 50) if plant["visible"] else (120, 120, 120)
        cv2.circle(annotated, (gx, gy), 7, marker_colour, -1)
        bx, by, bw, bh = plant["bbox"]
        if bw > 0 and bh > 0:
            cv2.rectangle(annotated, (x0 + bx, y0 + by), (x0 + bx + bw, y0 + by + bh), (80, 190, 255), 2)
        label = plant["slot_label"]
        if ppcm and plant["width_cm"] is not None and plant["height_cm"] is not None:
            size_text = f"{plant['width_cm']:.1f}x{plant['height_cm']:.1f}cm"
        else:
            size_text = f"{int(round(plant['width_px']))}x{int(round(plant['height_px']))}px"
        text = f"{label} {plant['canopy_coverage']:.1f}% {size_text} crowd:{plant['crowding_percentage']:.0f}%"
        cv2.putText(annotated, text, (gx + 9, gy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, marker_colour, 1, cv2.LINE_AA)

    stick = config.get("calibration_stick")
    if stick:
        start = normalized_point_to_pixels(stick["start"], frame.shape[1], frame.shape[0])
        end = normalized_point_to_pixels(stick["end"], frame.shape[1], frame.shape[0])
        cv2.line(annotated, start, end, (255, 200, 50), 3, cv2.LINE_AA)
        middle = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
        cv2.putText(annotated, f"{float(stick['length_cm']):g} cm", (middle[0] + 6, middle[1] - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 200, 50), 2, cv2.LINE_AA)

    status = "VALID" if image_valid else "CHECK FRAME"
    cv2.putText(
        annotated,
        f"LeafyCV1.0 | {config['lighting_mode']} | canopy {total_canopy:.1f}% | {status}",
        (15, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return annotated


def analyse_frame(
    *,
    frame: np.ndarray,
    config: dict[str, Any],
    output_root: Path,
    captured_at: datetime | None = None,
    api_client: CVApiClient | None = None,
    api_send_images: str = "raw",
) -> tuple[dict[str, Any], dict[str, Path]]:
    if not config.get("slots"):
        raise RuntimeError("No slot centres are registered. Run the calibration/registration command first.")

    captured_at = captured_at or datetime.now().astimezone()
    started = time.perf_counter()
    height, width = frame.shape[:2]
    roi = normalized_roi_to_pixels(config.get("roi"), width, height)
    x0, y0, rw, rh = roi
    zone = frame[y0 : y0 + rh, x0 : x0 + rw]
    centres_local = _slot_centres_local(config, width, height, roi)

    quality = evaluate_image_quality(
        zone,
        min_blur_score=float(config["analysis"]["min_blur_score"]),
        min_mean_brightness=float(config["analysis"]["min_mean_brightness"]),
        max_mean_brightness=float(config["analysis"]["max_mean_brightness"]),
    )
    masks = segment_vegetation(
        zone,
        str(config["lighting_mode"]).upper(),
        config["segmentation"],
        config["analysis"],
    )
    slot_map = build_slot_map(rw, rh, centres_local)
    ppcm = pixels_per_cm(config, width, height)
    plants = measure_slots(
        masks=masks,
        slot_map=slot_map,
        centres_local=centres_local,
        slots=config["slots"],
        lighting_mode=config["lighting_mode"],
        analysis_cfg=config["analysis"],
        pixels_per_cm=ppcm,
    )

    crowding = compute_crowding(
        mask=masks["combined"],
        slot_map=slot_map,
        plant_count=len(plants),
        gap_px=int(config["analysis"]["crowding_gap_px"]),
        min_contact_pixels=int(config["analysis"]["crowding_min_contact_pixels"]),
    )
    for index, plant in enumerate(plants, start=1):
        pid = f"P{index}"
        plant["crowding_percentage"] = float(crowding["per_plant_crowding_percent"].get(pid, 0.0))
        plant["touching_neighbors"] = list(crowding["per_plant_touching_neighbors"].get(pid, []))

    total_canopy = 100.0 * cv2.countNonZero(masks["combined"]) / max(1, masks["combined"].size)
    visible_count = sum(1 for item in plants if item["visible"])

    state_path = output_root / slugify(config["camera"]["name"]) / "state.json"
    state = load_state(state_path, config)
    final_image_valid, temporal_reasons = apply_growth_and_temporal_checks(
        results=plants,
        total_canopy=total_canopy,
        image_valid=bool(quality["measurement_valid"]),
        state=state,
        analysis_cfg=config["analysis"],
    )
    save_state(state_path, state)

    processing_time_ms = int(round((time.perf_counter() - started) * 1000.0))
    result: dict[str, Any] = {
        "model_version": MODEL_VERSION,
        "camera_id": config["camera"].get("camera_id"),
        "camera_name": config["camera"]["name"],
        "source_type": config["camera"]["source_type"],
        "captured_at": captured_at.isoformat(timespec="seconds"),
        "lighting_mode": str(config["lighting_mode"]).upper(),
        "size_calibrated": bool(ppcm),
        "calibration_pixels_per_cm": None if ppcm is None else round(float(ppcm), 6),
        "colour_measurement_valid": str(config["lighting_mode"]).upper() == "NORMAL",
        "roi_pixels": [x0, y0, rw, rh],
        "image_quality": {
            **quality,
            "temporal_reasons": temporal_reasons,
        },
        "analysis": {
            "total_canopy_coverage": round(float(total_canopy), 4),
            "visible_plant_count": int(visible_count),
            "measurement_valid": bool(final_image_valid),
            "processing_time_ms": processing_time_ms,
            "crowding_percentage": round(float(crowding["crowding_percent"]), 4),
        },
        "plants": plants,
    }

    annotated = _draw_annotation(
        frame=frame,
        roi=roi,
        slot_map=slot_map,
        centres_local=centres_local,
        plants=plants,
        config=config,
        ppcm=ppcm,
        total_canopy=total_canopy,
        image_valid=final_image_valid,
    )
    files = save_sample(
        output_root=output_root,
        result=result,
        frame=frame,
        annotated=annotated,
        mask=masks["combined"],
    )

    if api_client and api_client.enabled:
        api_client.send_sample(
            payload=build_backend_payload(result),
            raw_path=files["raw"],
            annotated_path=files["annotated"],
            mask_path=files["mask"],
            image_mode=api_send_images,
        )
    return result, files


def capture_and_analyse(
    *,
    config: dict[str, Any],
    output_root: Path,
    api_client: CVApiClient | None = None,
    api_send_images: str = "raw",
) -> tuple[dict[str, Any], dict[str, Path]]:
    frame = capture_frame(config)
    return analyse_frame(
        frame=frame,
        config=config,
        output_root=output_root,
        captured_at=datetime.now().astimezone(),
        api_client=api_client,
        api_send_images=api_send_images,
    )
