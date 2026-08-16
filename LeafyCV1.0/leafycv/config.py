from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

VALID_SOURCE_TYPES = {"WEBCAM", "RTSP", "FILE"}
VALID_LIGHTING_MODES = {"NORMAL", "MAGENTA"}

DEFAULT_ANALYSIS = {
    "interval_minutes": 30,
    "min_component_pixels": 150,
    "min_component_ratio": 0.00025,
    "visible_core_threshold": 0.03,
    "visible_area_threshold": 0.30,
    "crowding_gap_px": 3,
    "crowding_min_contact_pixels": 25,
    "min_blur_score": 15.0,
    "min_mean_brightness": 10.0,
    "max_mean_brightness": 245.0,
    "max_zone_change_pp": 20.0,
    "max_slot_change_pp": 20.0,
}

DEFAULT_SEGMENTATION = {
    "lower_h": 32,
    "upper_h": 95,
    "min_s": 55,
    "min_v": 35,
    "exg_threshold": 18,
    "lab_a_max": 150,
    "lab_b_min": 115,
    "magenta_min_s": 60,
    "magenta_max_v": 210,
}


def default_config() -> dict[str, Any]:
    return {
        "model_version": "LeafyCV1.0",
        "camera": {
            "camera_id": None,
            "name": "My Camera",
            "source_type": "WEBCAM",
            "enabled": True,
            "webcam_index": 0,
            "file_path": None,
            "rtsp": {
                "ip_address": None,
                "port": 554,
                "path": "",
                "username_env": "FARM_CAMERA_USER",
                "password_env": "FARM_CAMERA_PASSWORD",
            },
        },
        "lighting_mode": "NORMAL",
        "roi": None,
        "calibration_stick": None,
        "slots": [],
        "analysis": copy.deepcopy(DEFAULT_ANALYSIS),
        "segmentation": copy.deepcopy(DEFAULT_SEGMENTATION),
    }


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload = merge_defaults(payload)
    validate_config(payload)
    return payload


def save_config(path: str | Path, config: dict[str, Any]) -> None:
    validate_config(config)
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def merge_defaults(config: dict[str, Any]) -> dict[str, Any]:
    merged = default_config()
    for key, value in config.items():
        if key in {"camera", "analysis", "segmentation"} and isinstance(value, dict):
            merged[key].update(value)
            if key == "camera" and isinstance(value.get("rtsp"), dict):
                merged["camera"]["rtsp"] = {
                    **default_config()["camera"]["rtsp"],
                    **value["rtsp"],
                }
        else:
            merged[key] = value
    return merged


def _first_present(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def _unwrap_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("slot_positions", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def config_from_backend(camera_payload: dict[str, Any], slot_payload: Any) -> dict[str, Any]:
    """Convert Django API camera/slot records to the internal LeafyCV config."""
    if not isinstance(camera_payload, dict):
        raise ValueError("Backend camera configuration must be a JSON object.")
    # Support APIs that wrap the camera object in {"camera": {...}}.
    camera_data = camera_payload.get("camera") if isinstance(camera_payload.get("camera"), dict) else camera_payload

    config = default_config()
    camera = config["camera"]
    camera["camera_id"] = str(_first_present(camera_data, "camera_id", "id", default="")) or None
    camera["name"] = str(_first_present(camera_data, "name", default="Leafy Camera"))
    camera["source_type"] = str(_first_present(camera_data, "source_type", default="RTSP")).upper()
    camera["enabled"] = bool(_first_present(camera_data, "enabled", default=True))
    camera["webcam_index"] = int(_first_present(camera_data, "webcam_index", default=0) or 0)
    camera["rtsp"]["ip_address"] = _first_present(camera_data, "ip_address")
    camera["rtsp"]["port"] = int(_first_present(camera_data, "rtsp_port", default=554) or 554)
    camera["rtsp"]["path"] = str(_first_present(camera_data, "rtsp_path", default="") or "")
    config["lighting_mode"] = str(_first_present(camera_data, "lighting_mode", default="NORMAL")).upper()

    roi = _first_present(camera_data, "roi_points", "roi")
    if isinstance(roi, str) and roi.strip():
        try:
            roi = json.loads(roi)
        except json.JSONDecodeError:
            roi = None
    if isinstance(roi, dict):
        config["roi"] = {
            "x": float(roi["x"]),
            "y": float(roi["y"]),
            "width": float(roi["width"]),
            "height": float(roi["height"]),
        }

    sx = _first_present(camera_data, "calibration_start_x")
    sy = _first_present(camera_data, "calibration_start_y")
    ex = _first_present(camera_data, "calibration_end_x")
    ey = _first_present(camera_data, "calibration_end_y")
    length = _first_present(camera_data, "calibration_length_cm")
    if None not in (sx, sy, ex, ey, length):
        config["calibration_stick"] = {
            "start": [float(sx), float(sy)],
            "end": [float(ex), float(ey)],
            "length_cm": float(length),
        }

    slots: list[dict[str, Any]] = []
    for item in _unwrap_list(slot_payload):
        slot_value = item.get("slot")
        if isinstance(slot_value, dict):
            slot_id = _first_present(slot_value, "slot_id", "id")
            label = _first_present(item, "slot_label", default=_first_present(slot_value, "slot_number", "name", default=slot_id))
        else:
            slot_id = _first_present(item, "slot_id", default=slot_value)
            label = _first_present(item, "slot_label", "label", default=slot_id)
        if slot_id is None:
            continue
        cx = _first_present(item, "centre_x", "center_x")
        cy = _first_present(item, "centre_y", "center_y")
        if cx is None or cy is None:
            continue
        slots.append(
            {
                "slot_id": str(slot_id),
                "label": str(label),
                "centre": [float(cx), float(cy)],
            }
        )
    config["slots"] = slots
    validate_config(config)
    return config


def _check_normalized_point(point: Any, name: str) -> None:
    if not isinstance(point, list) or len(point) != 2:
        raise ValueError(f"{name} must be [x, y].")
    x, y = point
    if not (0.0 <= float(x) <= 1.0 and 0.0 <= float(y) <= 1.0):
        raise ValueError(f"{name} coordinates must be between 0 and 1.")


def validate_config(config: dict[str, Any]) -> None:
    camera = config.get("camera") or {}
    source_type = str(camera.get("source_type", "")).upper()
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError(f"camera.source_type must be one of {sorted(VALID_SOURCE_TYPES)}.")

    lighting = str(config.get("lighting_mode", "")).upper()
    if lighting not in VALID_LIGHTING_MODES:
        raise ValueError(f"lighting_mode must be one of {sorted(VALID_LIGHTING_MODES)}.")

    if source_type == "WEBCAM":
        try:
            int(camera.get("webcam_index", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("camera.webcam_index must be an integer.") from exc
    elif source_type == "FILE":
        if not camera.get("file_path"):
            raise ValueError("camera.file_path is required for FILE sources.")
    elif source_type == "RTSP":
        rtsp = camera.get("rtsp") or {}
        if not rtsp.get("ip_address"):
            raise ValueError("camera.rtsp.ip_address is required for RTSP sources.")

    roi = config.get("roi")
    if roi is not None:
        for field in ("x", "y", "width", "height"):
            if field not in roi:
                raise ValueError(f"roi.{field} is required when roi is set.")
        x = float(roi["x"])
        y = float(roi["y"])
        w = float(roi["width"])
        h = float(roi["height"])
        if not (0 <= x < 1 and 0 <= y < 1 and 0 < w <= 1 and 0 < h <= 1):
            raise ValueError("ROI values must be normalized between 0 and 1.")
        if x + w > 1.000001 or y + h > 1.000001:
            raise ValueError("ROI must remain inside the image.")

    stick = config.get("calibration_stick")
    if stick is not None:
        _check_normalized_point(stick.get("start"), "calibration_stick.start")
        _check_normalized_point(stick.get("end"), "calibration_stick.end")
        if float(stick.get("length_cm", 0)) <= 0:
            raise ValueError("calibration_stick.length_cm must be greater than zero.")

    seen_slot_ids: set[str] = set()
    for index, slot in enumerate(config.get("slots") or []):
        if "slot_id" not in slot:
            raise ValueError(f"slots[{index}].slot_id is required.")
        slot_id = str(slot["slot_id"])
        if slot_id in seen_slot_ids:
            raise ValueError(f"Duplicate slot_id in config: {slot_id}")
        seen_slot_ids.add(slot_id)
        _check_normalized_point(slot.get("centre"), f"slots[{index}].centre")


def normalized_roi_to_pixels(roi: dict | None, width: int, height: int) -> tuple[int, int, int, int]:
    if roi is None:
        return 0, 0, width, height
    x = int(round(float(roi["x"]) * width))
    y = int(round(float(roi["y"]) * height))
    w = int(round(float(roi["width"]) * width))
    h = int(round(float(roi["height"]) * height))
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = max(1, min(w, width - x))
    h = max(1, min(h, height - y))
    return x, y, w, h


def normalized_point_to_pixels(point: list[float], width: int, height: int) -> tuple[int, int]:
    x = int(round(float(point[0]) * max(1, width - 1)))
    y = int(round(float(point[1]) * max(1, height - 1)))
    return x, y


def pixels_to_normalized_point(x: int, y: int, width: int, height: int) -> list[float]:
    return [
        float(x) / max(1, width - 1),
        float(y) / max(1, height - 1),
    ]

# Backward-compatible helpers used by the interactive calibration GUI.
def pixel_point_to_normalized(point: tuple[int, int], width: int, height: int) -> list[float]:
    x, y = point
    return [round(float(x) / max(1, width), 6), round(float(y) / max(1, height), 6)]


def pixel_roi_to_normalized(roi: tuple[int, int, int, int], width: int, height: int) -> dict[str, float]:
    x, y, w, h = roi
    return {
        "x": round(float(x) / max(1, width), 6),
        "y": round(float(y) / max(1, height), 6),
        "width": round(float(w) / max(1, width), 6),
        "height": round(float(h) / max(1, height), 6),
    }
