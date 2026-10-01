"""LeafyAI physical TP-Link/Kasa powerboard configuration."""

from __future__ import annotations

import os

MODE = "kasa"
KASA_DISCOVERY_TIMEOUT = int(os.getenv("LEAFY_KASA_DISCOVERY_TIMEOUT", "5"))
KASA_RETRIES = max(1, int(os.getenv("LEAFY_KASA_RETRIES", "3")))
KASA_RETRY_DELAY_SECONDS = max(
    0.1,
    float(os.getenv("LEAFY_KASA_RETRY_DELAY_SECONDS", "0.75")),
)
KASA_USERNAME = os.getenv("LEAFY_KASA_USERNAME") or os.getenv("KASA_USERNAME") or ""
KASA_PASSWORD = os.getenv("LEAFY_KASA_PASSWORD") or os.getenv("KASA_PASSWORD") or ""

# Physical strip addresses come from deployment environment variables. The
# logical outlet map below is the contract used by the UI and AI actuator layer.
POWERBOARDS = {
    "board_1": {"ip": os.getenv("LEAFY_POWERBOARD_1_IP", "")},
    "board_2": {"ip": os.getenv("LEAFY_POWERBOARD_2_IP", "")},
}

# child_index refers to the outlet position reported by python-kasa for each strip.
DEVICES = {
    1: {"name": "pH Doser", "board": "board_1", "child_index": 0},
    2: {"name": "EC Doser", "board": "board_1", "child_index": 1},
    3: {"name": "Irrigation Pump", "board": "board_1", "child_index": 2},
    4: {"name": "Farm Fan", "board": "board_2", "child_index": 0},
    5: {"name": "Light Level 1", "board": "board_2", "child_index": 1},
    6: {"name": "Light Level 2", "board": "board_2", "child_index": 2},
}
