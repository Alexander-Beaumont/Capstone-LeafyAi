"""Parse the model's raw response into AIDecision fields."""

import json
import re


class Recommendation:
    """A parsed recommendation.

    Attributes:
        decision_type: str
        recommendation: str
        explanation: str
        confidence: float (0-1) or None
        used_fallback: bool — True if the model output was not valid JSON
                       and the raw text was kept as the recommendation.
    """

    def __init__(
        self,
        decision_type,
        recommendation,
        explanation,
        confidence,
        used_fallback,
        execution_type="notification",
        target_device="none",
        device_state="none",
        category="alert",
    ):
        self.decision_type = decision_type or "alert"
        self.execution_type = execution_type or "notification"
        self.target_device = target_device or "none"
        self.device_state = device_state or "none"
        self.category = category or "alert"
        self.recommendation = recommendation
        self.explanation = explanation
        self.confidence = confidence
        self.used_fallback = used_fallback

    def as_dict(self):
        return {
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
    """Remove an optional markdown ```json ... ``` fence around JSON."""
    text = raw.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def _clamp_confidence(value):
    """Return a float in [0, 1] (or None if the value is not usable)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, number))


def parse_recommendation(raw):
    """Convert a raw model response into a Recommendation.

    Best effort: if the model returns valid JSON (optionally fenced), map it
    to the AIDecision fields. Otherwise fall back to treating the whole text
    as the recommendation.
    """
    if raw is None:
        return Recommendation("alert", "", "", None, used_fallback=True)

    text = _strip_code_fence(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return Recommendation(
            decision_type="alert",
            recommendation=text,
            explanation="Model output was not valid JSON; stored as text.",
            confidence=None,
            used_fallback=True,
        )

    if not isinstance(data, dict):
        return Recommendation(
            decision_type="alert",
            recommendation=text,
            explanation="Model output was not a JSON object; stored as text.",
            confidence=None,
            used_fallback=True,
        )

    return Recommendation(
        decision_type=str(data.get("decision_type") or "alert"),
        execution_type=str(data.get("execution_type") or "notification"),
        target_device=str(data.get("target_device") or "none"),
        device_state=str(data.get("device_state") or "none"),
        category=str(data.get("category") or "alert"),
        recommendation=str(data.get("recommendation", "")),
        explanation=str(data.get("explanation", "")),
        confidence=_clamp_confidence(data.get("confidence")),
        used_fallback=False,
    )
