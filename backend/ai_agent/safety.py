"""Action-aware validation for persisted AI recommendations."""

import math
import re
from decimal import Decimal, InvalidOperation

from ai_agent.config_loader import load_farm_config
from ai_agent.models import SafetyCheck

CONFIDENCE_THRESHOLD = Decimal("0.70")
RELEVANT_SENSORS = {
    "climate": ("ambient_temperature", "humidity"),
    "dosing": ("ec", "ph"),
    "water": ("water_level", "water_temperature"),
}
VALID_CATEGORIES = {"climate", "lighting", "dosing", "water", "harvest", "alert"}
VALID_TARGETS = {"fans", "light", "none"}
VALID_STATES = {"on", "off", "none"}


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _device_state(farm_state, device_id):
    return next((item for item in farm_state.get("devices", []) if item.get("device_id") == device_id), None)


def _sensor_map(device_state):
    return {sensor.get("sensor_type"): sensor for sensor in device_state.get("sensors", []) if sensor.get("sensor_type")}


def _require_sensor(name, sensors, failures):
    sensor = sensors.get(name)
    if sensor is None:
        failures.append(f"{name} reading is missing.")
        return None
    if sensor.get("status") != "fresh":
        failures.append(f"{name} reading is {sensor.get('status') or 'missing'}.")
    if sensor.get("quality_status") == "suspect":
        failures.append(f"{name} reading is marked suspect.")
    value = _decimal(sensor.get("value"))
    if value is None:
        failures.append(f"{name} reading has no numeric value.")
    return value


def _range_position(value, limits):
    minimum = _decimal(limits.get("min"))
    maximum = _decimal(limits.get("max"))
    if value is None:
        return "unknown"
    if minimum is not None and value < minimum:
        return "below"
    if maximum is not None and value > maximum:
        return "above"
    return "within"


def _fan_direction_check(decision, values, ranges, failures):
    if decision.target_device != "fans":
        return
    temperature = values.get("ambient_temperature")
    humidity = values.get("humidity")
    hot = _range_position(temperature, ranges.get("ambient_temperature", {})) == "above"
    humid = _range_position(humidity, ranges.get("humidity", {})) == "above"
    condensation_risk = False
    if temperature is not None and humidity is not None and 0 < humidity <= 100:
        temp = float(temperature)
        rh = float(humidity)
        alpha = math.log(rh / 100.0) + (17.625 * temp) / (243.04 + temp)
        dew_point = Decimal(str((243.04 * alpha) / (17.625 - alpha)))
        offset = _decimal(ranges.get("dew_point", {}).get("min_offset_below_ambient"))
        condensation_risk = offset is not None and dew_point > temperature - offset
    needs_fan = hot or humid or condensation_risk
    if decision.device_state == "on" and not needs_fan:
        failures.append("Turning fans on is not supported by high temperature, humidity, or condensation risk.")
    if decision.device_state == "off" and needs_fan:
        failures.append("Turning fans off contradicts current temperature, humidity, or condensation evidence.")


def _has_active_batch(device_state):
    return any(area.get("current_batch") for level in device_state.get("levels", []) for area in level.get("growing_areas", []))


def _check_irrigation_duration(decision, ranges, failures):
    text = f"{decision.decision_type} {decision.recommendation}".lower()
    if "pump" not in text and "irrigation" not in text:
        return
    limits = ranges.get("irrigation_pump", {})
    minimum = _decimal(limits.get("min_on_mins"))
    maximum = _decimal(limits.get("max_on_mins"))
    for raw_value in re.findall(r"(\d+(?:\.\d+)?)\s*(?:min|mins|minute|minutes)", text):
        value = _decimal(raw_value)
        if minimum is not None and value < minimum:
            failures.append(f"Irrigation duration {value} minutes is below safe minimum {minimum}.")
        if maximum is not None and value > maximum:
            failures.append(f"Irrigation duration {value} minutes is above safe maximum {maximum}.")


def evaluate_safety(decision, farm_state, config=None):
    """Return a passed/failed result without blocking corrective recommendations."""
    config = config or load_farm_config()
    ranges = config.get("safety_ranges", {})
    failures = []
    evidence = {}
    if not decision.recommendation.strip():
        failures.append("Recommendation text is empty.")
    if decision.output_used_fallback:
        failures.append("Model output did not match the required JSON schema.")
    confidence = _decimal(decision.confidence_score)
    if confidence is None:
        failures.append("AI confidence is missing.")
    elif confidence < CONFIDENCE_THRESHOLD:
        failures.append(f"AI confidence {confidence} is below {CONFIDENCE_THRESHOLD}.")
    if decision.execution_type != "notification":
        failures.append("This release only permits notification recommendations.")
    if decision.category not in VALID_CATEGORIES:
        failures.append(f"Unknown recommendation category: {decision.category}.")
    if decision.target_device not in VALID_TARGETS:
        failures.append(f"Unknown target device: {decision.target_device}.")
    if decision.device_state not in VALID_STATES:
        failures.append(f"Unknown target state: {decision.device_state}.")
    if decision.target_device == "none" and decision.device_state != "none":
        failures.append("A recommendation without a target device must use state 'none'.")
    if decision.target_device != "none" and decision.device_state not in {"on", "off"}:
        failures.append("Fan/light recommendations must specify an on/off state.")
    if decision.target_device == "fans" and decision.category != "climate":
        failures.append("Fan target metadata is only valid for climate recommendations.")
    if decision.target_device == "light" and decision.category != "lighting":
        failures.append("Light target metadata is only valid for lighting recommendations.")
    if decision.category in {"dosing", "water", "harvest"} and (decision.target_device != "none" or decision.device_state != "none"):
        failures.append("High-risk notifications cannot contain executable target metadata.")

    device_state = _device_state(farm_state, decision.device_id)
    if device_state is None:
        failures.append(f"Device {decision.device_id} is absent from farm state.")
    else:
        sensors = _sensor_map(device_state)
        values = {}
        for name in RELEVANT_SENSORS.get(decision.category, ()):
            value = _require_sensor(name, sensors, failures)
            values[name] = value
            evidence[name] = {"value": float(value) if value is not None else None, "range_status": _range_position(value, ranges.get(name, {}))}
        if decision.category == "alert":
            fresh_values = [sensor for sensor in sensors.values() if sensor.get("status") == "fresh" and sensor.get("quality_status") != "suspect" and _decimal(sensor.get("value")) is not None]
            if not fresh_values:
                failures.append("A general alert requires at least one fresh numeric sensor.")
        if decision.category == "harvest" and not _has_active_batch(device_state):
            failures.append("A harvest recommendation requires an active crop batch.")
        _fan_direction_check(decision, values, ranges, failures)
        _check_irrigation_duration(decision, ranges, failures)

    result = "failed" if failures else "passed"
    explanation = " ".join(failures) if failures else "Recommendation is supported by fresh relevant evidence and policy checks."
    return {"result": result, "explanation": explanation, "failures": failures, "evidence": evidence}


def run_safety_check(decision, farm_state, config=None, persist=True):
    result = evaluate_safety(decision, farm_state, config=config)
    safety_check = None
    if persist:
        safety_check, _ = SafetyCheck.objects.update_or_create(decision=decision, defaults={"result": result["result"], "explanation": result["explanation"]})
    return {"id": safety_check.id if safety_check else None, "decision_id": decision.id, **result}
