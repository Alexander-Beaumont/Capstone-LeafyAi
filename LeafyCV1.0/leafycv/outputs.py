from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("_") or "camera"


def _csv_path(output_root: Path, camera_name: str) -> Path:
    return output_root / slugify(camera_name) / "measurements.csv"


def append_csv(path: Path, result: dict[str, Any], files: dict[str, Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    fields = [
        "model_version", "captured_at", "camera_name", "lighting_mode",
        "image_measurement_valid", "processing_time_ms", "size_calibrated",
        "slot_id", "slot_label", "visible", "measurement_valid",
        "canopy_area_px", "canopy_coverage", "width_px", "height_px",
        "width_cm", "height_cm", "green_percentage", "yellow_percentage",
        "brown_percentage_local_only", "colour_measurement_valid",
        "crowding_percentage", "growth_change", "raw_image", "annotated_image", "mask_image",
    ]
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        for plant in result["plants"]:
            writer.writerow(
                {
                    "model_version": result["model_version"],
                    "captured_at": result["captured_at"],
                    "camera_name": result["camera_name"],
                    "lighting_mode": result["lighting_mode"],
                    "image_measurement_valid": result["analysis"]["measurement_valid"],
                    "processing_time_ms": result["analysis"]["processing_time_ms"],
                    "size_calibrated": result["size_calibrated"],
                    "slot_id": plant["slot_id"],
                    "slot_label": plant["slot_label"],
                    "visible": plant["visible"],
                    "measurement_valid": plant["measurement_valid"],
                    "canopy_area_px": plant["canopy_area_px"],
                    "canopy_coverage": round(float(plant["canopy_coverage"]), 4),
                    "width_px": plant["width_px"],
                    "height_px": plant["height_px"],
                    "width_cm": plant["width_cm"],
                    "height_cm": plant["height_cm"],
                    "green_percentage": plant["green_percentage"],
                    "yellow_percentage": plant["yellow_percentage"],
                    "brown_percentage_local_only": plant["brown_percentage"],
                    "colour_measurement_valid": plant["colour_measurement_valid"],
                    "crowding_percentage": round(float(plant["crowding_percentage"]), 4),
                    "growth_change": round(float(plant["growth_change"]), 4),
                    "raw_image": files["raw"].as_posix(),
                    "annotated_image": files["annotated"].as_posix(),
                    "mask_image": files["mask"].as_posix(),
                }
            )


def save_sample(
    *,
    output_root: Path,
    result: dict[str, Any],
    frame: np.ndarray,
    annotated: np.ndarray,
    mask: np.ndarray,
) -> dict[str, Path]:
    camera_dir = output_root / slugify(result["camera_name"])
    camera_dir.mkdir(parents=True, exist_ok=True)
    stamp = result["captured_at"].replace(":", "").replace("-", "").replace("+", "_").replace("T", "_")
    stamp = stamp.split(".")[0]
    files = {
        "raw": camera_dir / f"{stamp}_raw.jpg",
        "annotated": camera_dir / f"{stamp}_annotated.jpg",
        "mask": camera_dir / f"{stamp}_mask.png",
        "json": camera_dir / f"{stamp}_result.json",
    }
    cv2.imwrite(str(files["raw"]), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    cv2.imwrite(str(files["annotated"]), annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    cv2.imwrite(str(files["mask"]), mask)
    files["json"].write_text(json.dumps(result, indent=2), encoding="utf-8")
    append_csv(_csv_path(output_root, result["camera_name"]), result, files)
    return files
