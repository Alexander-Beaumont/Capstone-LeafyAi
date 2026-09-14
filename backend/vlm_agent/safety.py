"""VLM safety persistence built on the shared recommendation safety rules."""

from ai_agent.safety import evaluate_safety
from vlm_agent.models import VLMSafetyCheck


def run_safety_check(decision, farm_state, visual_context, config=None, persist=True):
    result = evaluate_safety(decision, farm_state, config=config)
    if not visual_context["available"]:
        limitation = "Visual evidence was unavailable; this sensor-only VLM recommendation requires human review."
        result["reviews"].append(limitation)
        if result["result"] != "failed":
            result["result"] = "requires_review"
        result["explanation"] = f"{result['explanation']} {limitation}".strip()

    safety_check = None
    if persist:
        safety_check, _ = VLMSafetyCheck.objects.update_or_create(
            decision=decision,
            defaults={"result": result["result"], "explanation": result["explanation"]},
        )
    return {
        "id": safety_check.id if safety_check else None,
        "decision_id": decision.id,
        "result": result["result"],
        "explanation": result["explanation"],
        "confidence": result["confidence"],
    }
