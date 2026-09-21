"""Direct Camera <-> backend Powerboard lighting contract (no HTTP hop)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from powerboard_control.bridge import get_powerboard_bridge

VALID_STATES = {"ON", "OFF"}
class LightingControlError(RuntimeError): pass
@dataclass(frozen=True)
class LightingResult:
    success: bool
    state: str
class LightingController(Protocol):
    def get_state(self) -> LightingResult: ...
    def set_state(self, state: str) -> LightingResult: ...

class LocalLightingController:
    def exclusive_operation(self):
        return get_powerboard_bridge().exclusive_operation()

    def get_state(self) -> LightingResult:
        payload = get_powerboard_bridge().get_magenta_state()
        state = str(payload.get("state", "")).upper()
        if state not in {"ON", "OFF"}:
            raise LightingControlError(f"Magenta lighting is not in a restorable uniform state: {state or 'UNKNOWN'}")
        return LightingResult(bool(payload.get("success", True)), state)

    def set_state(self, state: str) -> LightingResult:
        requested = str(state).upper().strip()
        if requested not in VALID_STATES: raise ValueError("Lighting state must be ON or OFF")
        payload = get_powerboard_bridge().set_magenta_state(requested)
        confirmed = str(payload.get("state", requested)).upper()
        if not payload.get("success", True) or confirmed != requested:
            raise LightingControlError(f"Lighting requested {requested}, confirmed {confirmed}")
        return LightingResult(True, confirmed)
