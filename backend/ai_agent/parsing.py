"""Strict parsing for a multi-recommendation model response."""

import json
import re


class Recommendation:
    def __init__(self, device_id, decision_type, target_device, device_state, category, recommendation, explanation, confidence, used_fallback=False):
        self.device_id = device_id
        self.decision_type = decision_type or "alert"
        self.target_device = target_device or "none"
        self.device_state = device_state or "none"
        self.category = category or "alert"
        self.recommendation = recommendation
        self.explanation = explanation
        self.confidence = confidence
        self.used_fallback = used_fallback

    @property
    def execution_type(self):
        return "automated" if self.target_device in {"fans", "light"} and self.device_state in {"on", "off"} else "notification"

    def as_dict(self):
        return {
            "device_id": self.device_id,
            "decision_type": self.decision_type,
            "execution_type": self.execution_type,
            "target_device": self.target_device,
            "device_state": self.device_state,
            "category": self.category,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "confidence": self.confidence,
        }


def _strip_code_fence(raw):
    text = (raw or "").strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def _confidence(value):
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def parse_recommendations(raw, default_device_id=None):
    text = _strip_code_fence(raw)
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Model output was not valid JSON.")
    if not isinstance(payload, dict) or not isinstance(payload.get("recommendations"), list):
        raise ValueError("Model output must contain a recommendations list.")
    if not payload["recommendations"]:
        raise ValueError("Model output contained no recommendations.")

    recommendations = []
    for index, item in enumerate(payload["recommendations"]):
        if not isinstance(item, dict) or not str(item.get("recommendation") or "").strip():
            raise ValueError(f"Recommendation {index} is invalid.")
        recommendations.append(
            Recommendation(
                device_id=item.get("device_id") or default_device_id,
                decision_type=str(item.get("decision_type") or "alert"),
                target_device=str(item.get("target_device") or "none"),
                device_state=str(item.get("device_state") or "none"),
                category=str(item.get("category") or "alert"),
                recommendation=str(item["recommendation"]),
                explanation=str(item.get("explanation") or ""),
                confidence=_confidence(item.get("confidence")),
            )
        )
    observations = payload.get("image_observations") or []
    if not isinstance(observations, list):
        observations = []
    return observations, recommendations


def parse_recommendation(raw):
    """Compatibility helper returning the first item."""
    _, items = parse_recommendations(raw)
    return items[0]
