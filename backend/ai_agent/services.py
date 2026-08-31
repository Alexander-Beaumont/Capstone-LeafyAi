"""AI agent orchestration: turn farm state into a recommendation."""

from decimal import Decimal

from django.core.exceptions import ValidationError

from telemetry.models import Farm, FarmDevice
from farm_state.services import build_farm_state

from ai_agent.models import AIDecision
from ai_agent.parsing import parse_recommendation
from ai_agent.prompts import build_messages
from ai_agent.providers import get_provider
from ai_agent.safety import run_safety_check


class NoDeviceError(ValidationError):
    """Raised when a farm has no device to attach a decision to."""


def resolve_device(farm):
    """Return the farm's first device, or raise NoDeviceError."""
    device = FarmDevice.objects.filter(farm=farm).first()
    if device is None:
        raise NoDeviceError(
            f"Farm {farm.id} has no FarmDevice; a device is required "
            "to create an AIDecision."
        )
    return device


def generate_recommendation(farm, device=None, provider=None, persist=True):
    """Generate and optionally persist a recommendation for a farm.

    Args:
        farm (Farm): the farm to analyze.
        device (FarmDevice, optional): device to attach the decision to.
            Defaults to the farm's first device.
        provider (LLMProvider, optional): provider to call. Defaults to the
            provider selected by configuration (get_provider()).
        persist (bool): whether to write an AIDecision row.

    Returns:
        dict: farm id, device id, decision id (if persisted), the parsed
        recommendation, and the raw provider response.
    """
    device = device or resolve_device(farm)
    provider = provider or get_provider()

    farm_state = build_farm_state(farm)
    system, user = build_messages(farm_state)
    raw = provider.complete(system, user)
    parsed = parse_recommendation(raw)

    decision_id = None
    safety_check = None
    if persist:
        decision = AIDecision.objects.create(
            device=device,
            decision_type=parsed.decision_type,
            execution_type=parsed.execution_type,
            target_device=parsed.target_device,
            device_state=parsed.device_state,
            category=parsed.category,
            recommendation=parsed.recommendation,
            explanation=parsed.explanation,
            confidence_score=(
                Decimal(str(parsed.confidence)) if parsed.confidence is not None else None
            ),
        )
        decision_id = decision.id
        safety_check = run_safety_check(decision, farm_state, persist=True)

    return {
        "farm_id": farm.id,
        "device_id": device.id,
        "decision_id": decision_id,
        "recommendation": parsed.as_dict(),
        "safety_check": safety_check,
        "used_fallback": parsed.used_fallback,
        "raw": raw,
    }
