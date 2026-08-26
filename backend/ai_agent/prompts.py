"""Prompt building for the farm recommendation agent."""

import yaml
import json

def generate_system_prompt(config_path: str = "farm_config.yaml") -> str:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    crop = config["crop"]
    ranges = config["safety_ranges"]
    auto_devices = ", ".join(f"'{dev}'" for dev in config["execution_rules"]["automated_devices"])

    prompt = f"""You are an expert AI controller for a hydroponic {crop} vertical farm.
Analyze the provided JSON farm state and generate an actionable recommendation object.

Target Safety Ranges for {crop}:
- EC: {ranges['ec']['min']} - {ranges['ec']['max']} {ranges['ec']['unit']} ({ranges['ec']['action_note']})
- pH: {ranges['ph']['min']} - {ranges['ph']['max']}
- Water Temp: {ranges['water_temperature']['min']} - {ranges['water_temperature']['max']} {ranges['water_temperature']['unit']}
- Ambient Temp: {ranges['ambient_temperature']['min']} - {ranges['ambient_temperature']['max']} {ranges['ambient_temperature']['unit']}
- Humidity: {ranges['humidity']['min']} - {ranges['humidity']['max']}{ranges['humidity']['unit']}
- Dew Point: >{ranges['dew_point']['min_offset_below_ambient']} C below Ambient Temp
- Water Level: {ranges['water_level']['min']} - {ranges['water_level']['max']} {ranges['water_level']['unit']}
- Irrigation Pump: {ranges['irrigation_pump']['min_on_mins']} - {ranges['irrigation_pump']['max_on_mins']} {ranges['irrigation_pump']['unit']}

Execution Rules:
1. AUTOMATED: Controlling {auto_devices} on/off states.
2. NOTIFICATION: All other actions (e.g., Nutrient A/B dosing, pH adjustments, harvesting, water refill) cannot be automated and must be flagged for manual human action.

Respond with a single raw JSON object only (no markdown, no code blocks) using these exact keys:
- execution_type: 'automated' (only for {auto_devices} control) or 'notification'
- target_device: 'fans', 'light', or 'none'
- device_state: 'on', 'off', or 'none'
- category: 'climate', 'lighting', 'dosing', 'water', 'harvest', or 'alert'
- recommendation: concise action string for the user/dashboard
- explanation: 1-2 sentences explaining the sensor triggers
- confidence: float between 0.0 and 1.0"""

    return prompt

DEFAULT_SYSTEM = generate_system_prompt("farm_config.yaml")

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
