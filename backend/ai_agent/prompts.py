"""Prompts for sensor-only and raw-image farm recommendations."""
import json

from ai_agent.config_loader import load_farm_config


def generate_system_prompt(config_path=None, *, vision=False):
    config = load_farm_config(config_path)
    crop, ranges = config["crop"], config["safety_ranges"]
    visual = (
        "Inspect each labelled raw camera image directly and return one concise factual image_observations entry per visible camera. Do not invent details or use CV-derived measurements."
        if vision else
        "No reliable images are available. Return an empty image_observations list and reason only from farm data."
    )
    return f"""You are an expert hydroponic {crop} vertical-farm adviser.
Use current readings and trends; never treat missing, stale, or suspect data as reliable. {visual}

Target ranges: EC {ranges['ec']['min']}-{ranges['ec']['max']} {ranges['ec']['unit']}; pH {ranges['ph']['min']}-{ranges['ph']['max']}; water temperature {ranges['water_temperature']['min']}-{ranges['water_temperature']['max']} C; ambient temperature {ranges['ambient_temperature']['min']}-{ranges['ambient_temperature']['max']} C; humidity {ranges['humidity']['min']}-{ranges['humidity']['max']}%; water level {ranges['water_level']['min']}-{ranges['water_level']['max']} {ranges['water_level']['unit']}.

Return one raw JSON object with no markdown:
{{"image_observations":[{{"camera_id":1,"observation":"visible evidence"}}],"recommendations":[{{"device_id":1,"decision_type":"short_name","target_device":"fans|light|irrigation_pump|nutrient_doser|ph_doser|none","device_state":"on|off|none","category":"climate|lighting|dosing|water|harvest|alert","recommendation":"concise action","explanation":"evidence-based reason","confidence":0.0}}]}}

Return every material recommendation. Fan and light on/off recommendations may be executed after server safety checks. Every other target is advice only. Use only device_id values present in the farm JSON."""


def build_messages(farm_state):
    return generate_system_prompt(vision=False), "Current farm state:\n" + json.dumps(farm_state, default=str)


def build_vision_messages(farm_state, image_metadata):
    return (
        generate_system_prompt(vision=True),
        "Current farm state:\n" + json.dumps(farm_state, default=str) + "\n\nLabelled images follow in this metadata order:\n" + json.dumps(image_metadata, default=str),
    )
