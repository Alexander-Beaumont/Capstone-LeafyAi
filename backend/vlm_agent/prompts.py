"""Prompt construction for image-aware farm recommendations."""

import json

from ai_agent.prompts import generate_system_prompt


def build_messages(farm_state, visual_context):
    system = (
        generate_system_prompt()
        + "\n\nYou are also given visual evidence when available. "
        "Use sensor readings as independent evidence. Do not claim visual observations "
        "when visual_evidence.available is false."
    )
    user = (
        "Here is the current farm context as JSON. CV-derived canopy, crowding, and "
        "colour measurements are intentionally excluded:\n"
        + json.dumps(farm_state, default=str)
        + "\n\nVisual evidence metadata:\n"
        + json.dumps(visual_context, default=str)
        + "\n\nReturn the required recommendation JSON only."
    )
    return system, user
