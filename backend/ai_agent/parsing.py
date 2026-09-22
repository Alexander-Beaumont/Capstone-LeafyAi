"""Strict parsing for multi-recommendation model output."""
import json
import re


VALID_TARGETS = {"fans", "light", "irrigation_pump", "nutrient_doser", "ph_doser", "none"}
VALID_STATES = {"on", "off", "none"}
VALID_CATEGORIES = {"climate", "lighting", "dosing", "water", "harvest", "alert"}


class Recommendation:
    def __init__(self, device_id, decision_type, target_device, device_state, category, recommendation, explanation, confidence):
        self.device_id = device_id
        self.decision_type = decision_type or "alert"
        self.target_device = target_device
        self.device_state = device_state
        self.category = category
        self.recommendation = recommendation
        self.explanation = explanation
        self.confidence = confidence
        self.used_fallback = False

    @property
    def execution_type(self):
        return "automated" if self.target_device in {"fans", "light"} and self.device_state in {"on", "off"} else "notification"


def _strip_code_fence(raw):
    text = (raw or "").strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def _confidence(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, number))


def parse_recommendations(raw, default_device_id=None):
    try:
        payload = json.loads(_strip_code_fence(raw))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("Model output was not valid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("recommendations"), list):
        raise ValueError("Model output must contain a recommendations list.")
    if not payload["recommendations"]:
        raise ValueError("Model output contained no recommendations.")

    items = []
    for index, item in enumerate(payload["recommendations"]):
        if not isinstance(item, dict) or not str(item.get("recommendation") or "").strip():
            raise ValueError(f"Recommendation {index} is invalid.")
        target = str(item.get("target_device") or "none")
        state = str(item.get("device_state") or "none")
        category = str(item.get("category") or "alert")
        if target not in VALID_TARGETS or state not in VALID_STATES or category not in VALID_CATEGORIES:
            raise ValueError(f"Recommendation {index} contains an unsupported target, state, or category.")
        items.append(Recommendation(
            device_id=item.get("device_id") or default_device_id,
            decision_type=str(item.get("decision_type") or "alert"),
            target_device=target,
            device_state=state,
            category=category,
            recommendation=str(item["recommendation"]),
            explanation=str(item.get("explanation") or ""),
            confidence=_confidence(item.get("confidence")),
        ))
    observations = payload.get("image_observations") or []
    return observations if isinstance(observations, list) else [], items
