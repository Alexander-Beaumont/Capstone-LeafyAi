"""Prompt building for the farm recommendation agent."""

import json

DEFAULT_SYSTEM = (
    "You are an expert vertical-farming assistant. Given a JSON document "
    "describing the current state of a farm, produce a recommendation for "
    "the farm manager.\n\n"
    "Respond with a single JSON object only, with exactly these keys:\n"
    "- decision_type: one of 'schedule_update', 'dosing_adjustment', "
    "'lighting_adjustment', 'fan_adjustment', 'harvest_recommendation', "
    "'spacing_adjustment', or 'alert'\n"
    "- recommendation: a short, concrete action or advice string\n"
    "- explanation: one or two sentences explaining why\n"
    "- confidence: a number between 0 and 1\n\n"
    "Do not include commentary, markdown fences, or anything outside the JSON object."
)


def build_messages(farm_state):
    """Build (system, user) message strings for the provider.

    Args:
        farm_state: dict produced by farm_state.services.build_farm_state.

    Returns:
        tuple[str, str]: (system prompt, user prompt).
    """
    user = (
        "Here is the current farm state as JSON:\n"
        + json.dumps(farm_state, default=str)
        + "\n\n"
        "Review it and return your recommendation as JSON."
    )
    return DEFAULT_SYSTEM, user
