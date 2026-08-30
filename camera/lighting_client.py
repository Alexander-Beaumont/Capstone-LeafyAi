"""Optional Camera <-> Lighting/Switch HTTP interface.

The lighting teammate owns the relay/GPIO/ESP32/etc.  The Camera service only
needs a tiny ON/OFF interface.  If the teammate uses MQTT or a Python module
instead of HTTP, replace this file while preserving the set_state() contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import requests


VALID_STATES = {"ON", "OFF"}


class LightingControlError(RuntimeError):
    """Raised when the lighting controller cannot confirm a requested state."""


@dataclass(frozen=True)
class LightingResult:
    """Normalized result returned by the lighting controller."""

    success: bool
    state: str


class LightingController(Protocol):
    """Small interface used by CameraCollector; hardware details stay outside."""

    def set_state(self, state: str) -> LightingResult: ...


class HttpLightingController:
    """HTTP implementation of the Camera <-> Lighting/Switch contract.

    Expected request:
        POST <base_url><state_path>
        {"state": "OFF"}   or   {"state": "ON"}

    Preferred response:
        {"success": true, "state": "OFF"}

    The endpoint is intentionally configurable because the lighting teammate
    may host it in a separate actuator/sensor service.
    """

    def __init__(
        self,
        base_url: str,
        *,
        state_path: str = "/api/lighting/magenta/state/",
        access_token: str = "",
        timeout: float = 5.0,
        require_confirmation: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.state_path = "/" + state_path.lstrip("/")
        self.access_token = access_token.strip()
        self.timeout = max(1.0, float(timeout))
        self.require_confirmation = bool(require_confirmation)

        if not self.base_url:
            raise ValueError("Lighting base URL is required when lighting control is enabled.")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def set_state(self, state: str) -> LightingResult:
        """Request ON/OFF and optionally require the controller to confirm it."""
        requested = str(state).upper().strip()
        if requested not in VALID_STATES:
            raise ValueError(f"Lighting state must be one of {sorted(VALID_STATES)}.")

        response = requests.post(
            f"{self.base_url}{self.state_path}",
            json={"state": requested},
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()

        # A JSON confirmation is strongly preferred for official captures.
        payload = response.json() if response.content else {}
        success = bool(payload.get("success", True)) if isinstance(payload, dict) else True
        confirmed_state = (
            str(payload.get("state", requested)).upper()
            if isinstance(payload, dict)
            else requested
        )

        if not success:
            raise LightingControlError(f"Lighting controller rejected state {requested}.")

        if self.require_confirmation:
            if not isinstance(payload, dict) or "state" not in payload:
                raise LightingControlError(
                    "Lighting response did not include a confirmed 'state'."
                )
            if confirmed_state != requested:
                raise LightingControlError(
                    f"Lighting requested {requested} but controller reported {confirmed_state}."
                )

        return LightingResult(success=True, state=confirmed_state)
