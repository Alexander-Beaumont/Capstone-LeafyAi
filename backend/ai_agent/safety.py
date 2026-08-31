"""Safety validation for AI-generated farm recommendations."""

import re
from decimal import Decimal, InvalidOperation

from ai_agent.config_loader import load_farm_config
from ai_agent.models import SafetyCheck


CONFIDENCE_REVIEW_THRESHOLD = Decimal("0.70")


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _device_state(farm_state, device_id):
    for device in farm_state.get("devices", []):
        if device.get("device_id") == device_id:
            return device
    return None


def rollup_farm_state_confidence(farm_state, device_id=None):
    """Summarise freshness for farm-state values."""
    statuses = {"fresh": 0, "stale": 0, "missing": 0}

    devices = farm_state.get("devices", [])
    if device_id is not None:
        devices = [device for device in devices if device.get("device_id") == device_id]

    for device in devices:
        for sensor in device.get("sensors", []):
            status = sensor.get("status")
            if status in statuses:
                statuses[status] += 1

        tank = device.get("nutrient_tank")
        if tank:
            status = tank.get("status")
            if status in statuses:
                statuses[status] += 1
        else:
            statuses["missing"] += 1

        for level in device.get("levels", []):
            for camera in level.get("cameras", []):
                status = camera.get("status")
                if status in statuses:
                    statuses[status] += 1

    if statuses["missing"] or statuses["stale"]:
        confidence_level = "low" if statuses["missing"] else "medium"
    else:
        confidence_level = "high"

    return {
        "fresh_count": statuses["fresh"],
        "stale_count": statuses["stale"],
        "missing_count": statuses["missing"],
        "confidence_level": confidence_level,
    }


def _sensor_map(device_state):
    return {
        sensor.get("sensor_type"): sensor
        for sensor in device_state.get("sensors", [])
        if sensor.get("sensor_type")
    }


def _check_range(name, state, config_range, failures, reviews):
    if state is None:
        reviews.append(f"{name} reading is missing.")
        return

    status = state.get("status")
    if status in ("missing", "stale"):
        reviews.append(f"{name} reading is {status}.")

    value = _decimal(state.get("value"))
    if value is None:
        reviews.append(f"{name} reading has no numeric value.")
        return

    min_value = _decimal(config_range.get("min"))
    max_value = _decimal(config_range.get("max"))

    if min_value is not None and value < min_value:
        failures.append(f"{name} value {value} is below safe minimum {min_value}.")
    if max_value is not None and value > max_value:
        failures.append(f"{name} value {value} is above safe maximum {max_value}.")


def _check_dew_point(sensor_states, config_range, failures, reviews):
    dew_state = sensor_states.get("dew_point")
    ambient_state = sensor_states.get("ambient_temperature")
    _check_range("dew_point", dew_state, config_range, failures, reviews)

    dew_value = _decimal(dew_state.get("value")) if dew_state else None
    ambient_value = _decimal(ambient_state.get("value")) if ambient_state else None
    min_offset = _decimal(config_range.get("min_offset_below_ambient"))

    if ambient_state is None:
        reviews.append("ambient_temperature is required for dew point offset check.")
        return
    if ambient_state.get("status") in ("missing", "stale"):
        reviews.append(
            f"ambient_temperature reading is {ambient_state.get('status')} for dew point offset check."
        )
    if dew_value is None or ambient_value is None or min_offset is None:
        return
    if dew_value > ambient_value - min_offset:
        failures.append(
            f"dew_point must be at least {min_offset} C below ambient_temperature."
        )


def _check_irrigation_pump_text(decision, config_range, failures):
    text = f"{decision.decision_type} {decision.category} {decision.recommendation}".lower()
    if "pump" not in text and "irrigation" not in text:
        return

    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:min|mins|minute|minutes)", text)
    if not matches:
        return

    min_on = _decimal(config_range.get("min_on_mins"))
    max_on = _decimal(config_range.get("max_on_mins"))
    for raw in matches:
        value = _decimal(raw)
        if value is None:
            continue
        if min_on is not None and value < min_on:
            failures.append(f"irrigation_pump duration {value} mins is below safe minimum {min_on}.")
        if max_on is not None and value > max_on:
            failures.append(f"irrigation_pump duration {value} mins is above safe maximum {max_on}.")


def evaluate_safety(decision, farm_state, config=None):
    """Return a safety result dict for a decision without writing it."""
    config = config or load_farm_config()
    ranges = config.get("safety_ranges", {})
    execution_rules = config.get("execution_rules", {})
    automated_devices = set(execution_rules.get("automated_devices", []))
    manual_categories = {"dosing", "water", "harvest"}

    failures = []
    reviews = []

    device_state = _device_state(farm_state, decision.device_id)
    if device_state is None:
        failures.append(f"Device {decision.device_id} is absent from farm state.")
        confidence = rollup_farm_state_confidence(farm_state)
    else:
        confidence = rollup_farm_state_confidence(
            farm_state, device_id=decision.device_id
        )
        sensor_states = _sensor_map(device_state)

        for name, config_range in ranges.items():
            if name == "irrigation_pump":
                _check_irrigation_pump_text(decision, config_range, failures)
            elif name == "dew_point":
                _check_dew_point(sensor_states, config_range, failures, reviews)
            else:
                _check_range(name, sensor_states.get(name), config_range, failures, reviews)

    if decision.execution_type == "automated":
        if decision.target_device not in automated_devices:
            failures.append(
                f"{decision.target_device} is not configured for automated execution."
            )
        if decision.device_state not in ("on", "off"):
            failures.append("Automated actions must specify device_state on or off.")
    elif decision.execution_type != "notification":
        failures.append(f"{decision.execution_type} is not a valid execution_type.")

    if decision.category in manual_categories:
        reviews.append(f"{decision.category} actions require human review.")

    confidence_score = _decimal(decision.confidence_score)
    if confidence_score is None:
        reviews.append("AI confidence is missing.")
    elif confidence_score < CONFIDENCE_REVIEW_THRESHOLD:
        reviews.append(
            f"AI confidence {confidence_score} is below {CONFIDENCE_REVIEW_THRESHOLD}."
        )

    if confidence["confidence_level"] != "high":
        reviews.append(
            "Farm state confidence is "
            f"{confidence['confidence_level']} "
            f"(fresh={confidence['fresh_count']}, stale={confidence['stale_count']}, "
            f"missing={confidence['missing_count']})."
        )

    if failures:
        result = "failed"
        reasons = failures + reviews
    elif reviews:
        result = "requires_review"
        reasons = reviews
    else:
        result = "passed"
        reasons = [
            "All configured safety ranges passed with high-confidence farm state."
        ]

    return {
        "result": result,
        "explanation": " ".join(reasons),
        "confidence": confidence,
        "failures": failures,
        "reviews": reviews,
    }


def run_safety_check(decision, farm_state, config=None, persist=True):
    """Evaluate and optionally persist a SafetyCheck for an AI decision."""
    result = evaluate_safety(decision, farm_state, config=config)
    safety_check = None
    if persist:
        safety_check, _ = SafetyCheck.objects.update_or_create(
            decision=decision,
            defaults={
                "result": result["result"],
                "explanation": result["explanation"],
            },
        )

    return {
        "id": safety_check.id if safety_check else None,
        "decision_id": decision.id,
        "result": result["result"],
        "explanation": result["explanation"],
        "confidence": result["confidence"],
    }
