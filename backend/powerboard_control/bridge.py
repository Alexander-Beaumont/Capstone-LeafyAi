"""Thread-safe synchronous bridge to the async python-kasa controller.

Django views and Camera capture share one controller/event loop, so no internal
HTTP service or extra Docker container is required.
"""
from __future__ import annotations
import asyncio, threading
from contextlib import contextmanager
from concurrent.futures import Future
from typing import Any, Coroutine
from .kasa_service import PowerboardController


class PowerboardBridge:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._controller: PowerboardController | None = None
        self._ready = threading.Event()
        self._operation_lock = threading.RLock()
        self._thread = threading.Thread(target=self._run, name="leafy-powerboard-loop", daemon=True)
        self._thread.start(); self._ready.wait(timeout=5)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._controller = PowerboardController()
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

    @contextmanager
    def exclusive_operation(self):
        """Serialize multi-call hardware transactions across runtime services."""
        with self._operation_lock:
            yield self

    def get_all_device_statuses(self):
        with self._operation_lock: return self._call(self.controller.get_all_device_statuses())
    def set_device_state(self, device_id: int, state: str):
        with self._operation_lock: return self._call(self.controller.set_device_state(device_id, state))
    def get_magenta_state(self):
        with self._operation_lock: return self._call(self.controller.get_magenta_state())
    def set_magenta_state(self, state: str):
        with self._operation_lock: return self._call(self.controller.set_magenta_state(state))


_BRIDGE: PowerboardBridge | None = None
_LOCK = threading.Lock()

def get_powerboard_bridge() -> PowerboardBridge:
    global _BRIDGE
    with _LOCK:
        if _BRIDGE is None:
            _BRIDGE = PowerboardBridge()
        return _BRIDGE
