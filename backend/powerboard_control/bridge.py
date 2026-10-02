"""Thread-safe synchronous bridge to the async python-kasa controller."""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine

from .kasa_service import PowerboardController


class PowerboardBridge:
    def __init__(self, powerboards=None) -> None:
        # Django request handlers are synchronous, while python-kasa is async.
        # A dedicated daemon event loop lets both callers share one controller.
        self._loop = asyncio.new_event_loop()
        self._powerboards = powerboards
        self._controller: PowerboardController | None = None
        self._ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="leafy-powerboard-loop",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._controller = PowerboardController(powerboards=self._powerboards)
        self._ready.set()
        self._loop.run_forever()

    def _call(self, coro: Coroutine[Any, Any, Any], timeout: float = 30.0):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    @property
    def controller(self) -> PowerboardController:
        if self._controller is None:
            raise RuntimeError("Powerboard runtime is not ready")
        return self._controller

    def get_all_device_statuses(self):
        return self._call(self.controller.get_all_device_statuses())

    def set_device_state(self, device_id: int, state: str):
        return self._call(self.controller.set_device_state(device_id, state))


_BRIDGES: dict[tuple[str, str], PowerboardBridge] = {}
_LOCK = threading.Lock()


def _bridge_key(powerboards) -> tuple[str, str]:
    if powerboards is None:
        from .config import POWERBOARDS

        powerboards = POWERBOARDS
    return (
        str(powerboards.get("board_1", {}).get("ip") or ""),
        str(powerboards.get("board_2", {}).get("ip") or ""),
    )


def get_powerboard_bridge(powerboards=None) -> PowerboardBridge:
    # Reuse one event-loop/controller per physical pair. Calling this with no
    # argument preserves the existing environment-variable based behaviour.
    key = _bridge_key(powerboards)
    with _LOCK:
        bridge = _BRIDGES.get(key)
        if bridge is None:
            bridge = PowerboardBridge(powerboards=powerboards)
            _BRIDGES[key] = bridge
        return bridge
