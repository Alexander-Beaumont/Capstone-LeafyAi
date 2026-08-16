from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def layout_fingerprint(config: dict[str, Any]) -> str:
    stable = {
        "camera_name": config["camera"]["name"],
        "source_type": config["camera"].get("source_type"),
        "lighting_mode": config.get("lighting_mode"),
        "roi": config.get("roi"),
        "slots": [
            {"slot_id": str(slot["slot_id"]), "centre": slot["centre"]}
            for slot in config.get("slots") or []
        ],
    }
    raw = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def load_state(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    expected = layout_fingerprint(config)
    if not path.exists():
        return {"layout_fingerprint": expected, "last_total_canopy": None, "last_slots": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"layout_fingerprint": expected, "last_total_canopy": None, "last_slots": {}}
    if state.get("layout_fingerprint") != expected:
        return {"layout_fingerprint": expected, "last_total_canopy": None, "last_slots": {}}
    state.setdefault("last_total_canopy", None)
    state.setdefault("last_slots", {})
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def apply_growth_and_temporal_checks(
    *,
    results: list[dict],
    total_canopy: float,
    image_valid: bool,
    state: dict[str, Any],
    analysis_cfg: dict,
) -> tuple[bool, list[str]]:
    """Attach growth_change and reject implausible abrupt canopy jumps.

    Valid measurements update the persistent baseline. Invalid measurements are
    saved for evidence but do not replace the next growth baseline.
    """
    reasons: list[str] = []
    final_image_valid = bool(image_valid)
    previous_total = state.get("last_total_canopy")
    if previous_total is not None:
        zone_change = abs(float(total_canopy) - float(previous_total))
        if zone_change > float(analysis_cfg["max_zone_change_pp"]):
            final_image_valid = False
            reasons.append("whole_zone_canopy_jump")

    last_slots: dict[str, float] = state.get("last_slots", {})
    candidate_updates: dict[str, float] = {}
    for item in results:
        key = str(item["slot_id"])
        current = float(item["canopy_coverage"])
        previous = last_slots.get(key)
        item["growth_change"] = 0.0 if previous is None else current - float(previous)
        slot_valid = bool(item.get("measurement_valid", False) and final_image_valid)
        if previous is not None:
            if abs(current - float(previous)) > float(analysis_cfg["max_slot_change_pp"]):
                slot_valid = False
                reasons.append(f"slot_canopy_jump:{key}")
        item["measurement_valid"] = slot_valid
        if slot_valid:
            candidate_updates[key] = current

    if final_image_valid:
        state["last_total_canopy"] = float(total_canopy)
    for key, value in candidate_updates.items():
        last_slots[key] = float(value)
    state["last_slots"] = last_slots
    return final_image_valid, sorted(set(reasons))
