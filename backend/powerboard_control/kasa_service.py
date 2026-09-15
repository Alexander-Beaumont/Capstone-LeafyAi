from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from .config import (
    DEVICES,
    KASA_DISCOVERY_TIMEOUT,
    KASA_PASSWORD,
    KASA_RETRY_DELAY_SECONDS,
    KASA_RETRIES,
    KASA_USERNAME,
    MAGENTA_LIGHT_DEVICE_IDS,
    MODE,
    POWERBOARDS,
)


class PowerboardController:
    """Real TP-Link/Kasa powerboard controller.

    Important runtime behaviour for KP303 strips:
    - Discover each physical strip once per logical operation, not once per outlet.
    - Read/update the strip once, then use its child outlets.
    - Retry transient Kasa transport failures with a fresh discovery.

    This avoids hammering a KP303 with several immediate discover/update cycles, which
    can cause intermittent legacy-protocol reads such as "0 bytes read on a total of
    4 expected bytes" even though a one-shot probe succeeds.
    """

    def __init__(self):
        self.mode = MODE
        self._lock = asyncio.Lock()

    def _discover_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "discovery_timeout": KASA_DISCOVERY_TIMEOUT,
            "timeout": KASA_DISCOVERY_TIMEOUT,
        }
        if KASA_USERNAME and KASA_PASSWORD:
            kwargs["username"] = KASA_USERNAME
            kwargs["password"] = KASA_PASSWORD
        return kwargs

    async def _connect_board(self, board_key: str):
        """Discover + update one real strip, retrying transient transport failures."""
        from kasa import Discover

        board = POWERBOARDS[board_key]
        ip = str(board.get("ip") or "").strip()
        if not ip:
            raise RuntimeError(f"NOT_CONFIGURED: {board_key} has no IP configured")
        last_exc: Exception | None = None

        for attempt in range(1, KASA_RETRIES + 1):
            try:
                device = await Discover.discover_single(ip, **self._discover_kwargs())
                if device is None:
                    raise RuntimeError("no supported Kasa device discovered")
                await device.update()
                return device
            except Exception as exc:  # fresh discovery on the next attempt
                last_exc = exc
                if attempt < KASA_RETRIES:
                    await asyncio.sleep(KASA_RETRY_DELAY_SECONDS * attempt)

        credential_hint = (
            " TP-Link/Kasa credentials are configured."
            if KASA_USERNAME and KASA_PASSWORD
            else " If this is a newer authenticated Kasa device, set LEAFY_KASA_USERNAME and LEAFY_KASA_PASSWORD in .env.real."
        )
        raise RuntimeError(
            f"Unable to query Kasa powerboard {board_key} at {ip} after {KASA_RETRIES} attempt(s): "
            f"{last_exc}.{credential_hint}"
        ) from last_exc

    @staticmethod
    def _children(board) -> list[Any]:
        return list(board.children or [])

    def _plug_for(self, board, device_id: int):
        info = DEVICES[device_id]
        children = self._children(board)
        index = info["child_index"]
        if index < 0 or index >= len(children):
            model = getattr(board, "model", "unknown")
            alias = getattr(board, "alias", None)
            raise RuntimeError(
                f"Kasa child_index {index} invalid for device {device_id} on {info['board']} "
                f"({POWERBOARDS[info['board']]['ip']}, model={model}, alias={alias!r}, children={len(children)})"
            )
        return children[index]

    async def _refresh_board(self, board_key: str, board):
        """Refresh an already connected strip; rediscover if its transport went stale."""
        last_exc: Exception | None = None
        for attempt in range(1, KASA_RETRIES + 1):
            try:
                await board.update()
                return board
            except Exception as exc:
                last_exc = exc
                if attempt < KASA_RETRIES:
                    await asyncio.sleep(KASA_RETRY_DELAY_SECONDS * attempt)
                    board = await self._connect_board(board_key)
        raise RuntimeError(
            f"Unable to refresh Kasa powerboard {board_key} at {POWERBOARDS[board_key]['ip']}: {last_exc}"
        ) from last_exc

    async def set_device_state(self, device_id: int, state: str) -> dict[str, Any]:
        requested = state.upper().strip()
        if requested not in {"ON", "OFF"}:
            raise ValueError("state must be ON or OFF")
        if device_id not in DEVICES:
            raise KeyError(f"Unknown device_id {device_id}")

        info = DEVICES[device_id]
        board_key = info["board"]
        async with self._lock:
            board = await self._connect_board(board_key)
            plug = self._plug_for(board, device_id)
            if requested == "ON":
                await plug.turn_on()
            else:
                await plug.turn_off()
            board = await self._refresh_board(board_key, board)
            confirmed = bool(self._plug_for(board, device_id).is_on)

        if confirmed != (requested == "ON"):
            raise RuntimeError(
                f"Device {device_id} requested {requested} but hardware confirmed {'ON' if confirmed else 'OFF'}"
            )
        return self._status(device_id, confirmed)

    async def _restore_magenta_on(self, board_key: str, board=None) -> None:
        """Best-effort safety restore used only after an OFF failure."""
        try:
            if board is None:
                board = await self._connect_board(board_key)
            for device_id in MAGENTA_LIGHT_DEVICE_IDS:
                if DEVICES[device_id]["board"] != board_key:
                    continue
                try:
                    await self._plug_for(board, device_id).turn_on()
                except Exception:
                    pass
            try:
                await self._refresh_board(board_key, board)
            except Exception:
                pass
        except Exception:
            pass

    async def get_magenta_state(self) -> dict[str, Any]:
        """Return ON only when both configured magenta-light outlets are ON."""
        board_keys = {DEVICES[device_id]["board"] for device_id in MAGENTA_LIGHT_DEVICE_IDS}
        if len(board_keys) != 1:
            raise RuntimeError("MAGENTA_LIGHT_DEVICE_IDS must currently map to one physical powerboard")
        board_key = next(iter(board_keys))

        async with self._lock:
            board = await self._connect_board(board_key)
            statuses = [
                self._status(device_id, bool(self._plug_for(board, device_id).is_on))
                for device_id in MAGENTA_LIGHT_DEVICE_IDS
            ]

        states = {row["state"] for row in statuses}
        state = "ON" if states == {"ON"} else "OFF" if states == {"OFF"} else "MIXED"
        return {"success": True, "state": state, "devices": statuses}

    async def set_magenta_state(self, state: str) -> dict[str, Any]:
        """Treat both grow-light outlets as one capture-lighting unit.

        Both LeafyAI grow-light outlets are on the same KP303 in the locked hardware
        mapping. We therefore discover/update that strip once, actuate both children,
        then refresh once and confirm both. If OFF partially fails, both outlets are
        restored ON before the API returns an error.
        """
        requested = state.upper().strip()
        if requested not in {"ON", "OFF"}:
            raise ValueError("state must be ON or OFF")

        board_keys = {DEVICES[device_id]["board"] for device_id in MAGENTA_LIGHT_DEVICE_IDS}
        if len(board_keys) != 1:
            raise RuntimeError("MAGENTA_LIGHT_DEVICE_IDS must currently map to one physical powerboard")
        board_key = next(iter(board_keys))

        async with self._lock:
            board = await self._connect_board(board_key)
            try:
                for device_id in MAGENTA_LIGHT_DEVICE_IDS:
                    plug = self._plug_for(board, device_id)
                    if requested == "ON":
                        await plug.turn_on()
                    else:
                        await plug.turn_off()

                board = await self._refresh_board(board_key, board)
                results: list[dict[str, Any]] = []
                for device_id in MAGENTA_LIGHT_DEVICE_IDS:
                    confirmed = bool(self._plug_for(board, device_id).is_on)
                    if confirmed != (requested == "ON"):
                        raise RuntimeError(
                            f"Device {device_id} requested {requested} but hardware confirmed "
                            f"{'ON' if confirmed else 'OFF'}"
                        )
                    results.append(self._status(device_id, confirmed))
            except Exception:
                if requested == "OFF":
                    await self._restore_magenta_on(board_key, board)
                raise

        return {"success": True, "state": requested, "devices": results}

    def _status(self, device_id: int, is_on: bool) -> dict[str, Any]:
        info = DEVICES[device_id]
        board_key = info["board"]
        return {
            "device_id": device_id,
            "name": info["name"],
            "board": board_key,
            "board_ip": POWERBOARDS[board_key]["ip"],
            "child_index": info["child_index"],
            "is_on": bool(is_on),
            "state": "ON" if is_on else "OFF",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_device_status(self, device_id: int) -> dict[str, Any]:
        if device_id not in DEVICES:
            raise KeyError(f"Unknown device_id {device_id}")
        info = DEVICES[device_id]
        async with self._lock:
            board = await self._connect_board(info["board"])
            plug = self._plug_for(board, device_id)
            return self._status(device_id, bool(plug.is_on))

    async def get_all_device_statuses(self) -> list[dict[str, Any]]:
        """Read all six logical devices with only one network query per physical strip."""
        rows: list[dict[str, Any]] = []
        async with self._lock:
            for board_key in POWERBOARDS:
                device_ids = [device_id for device_id, info in DEVICES.items() if info["board"] == board_key]
                try:
                    board = await self._connect_board(board_key)
                    for device_id in device_ids:
                        plug = self._plug_for(board, device_id)
                        rows.append(self._status(device_id, bool(plug.is_on)))
                except Exception as exc:
                    not_configured = str(exc).startswith("NOT_CONFIGURED:")
                    for device_id in device_ids:
                        info = DEVICES[device_id]
                        rows.append(
                            {
                                "device_id": device_id,
                                "name": info["name"],
                                "board": board_key,
                                "board_ip": POWERBOARDS[board_key]["ip"],
                                "child_index": info["child_index"],
                                "is_on": None,
                                "state": "NOT CONFIGURED" if not_configured else "ERROR",
                                "error": str(exc),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
        return rows
