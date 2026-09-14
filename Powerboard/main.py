from __future__ import annotations

import asyncio
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import MAGENTA_LIGHT_DEVICE_IDS, MODE, WATCHDOG_SECONDS
from kasa_service import PowerboardController

app = FastAPI(title="LeafyAI Powerboard / Lighting MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local MVP service; restrict this for production deployment
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
controller = PowerboardController()
magenta_off_since: float | None = None
watchdog_task: asyncio.Task | None = None


class StateRequest(BaseModel):
    state: str


@app.on_event("startup")
async def start_watchdog():
    global watchdog_task
    watchdog_task = asyncio.create_task(_watchdog_loop())


@app.on_event("shutdown")
async def stop_watchdog():
    if watchdog_task:
        watchdog_task.cancel()


async def _watchdog_loop():
    global magenta_off_since
    while True:
        await asyncio.sleep(1)
        if magenta_off_since is None:
            continue
        if time.monotonic() - magenta_off_since >= WATCHDOG_SECONDS:
            try:
                result = await controller.set_magenta_state("ON")
                if result["success"]:
                    print("Lighting watchdog auto-restored grow lights ON.")
                    magenta_off_since = None
            except Exception as exc:
                print(f"Lighting watchdog restore warning: {exc}")


@app.get("/health/")
async def health():
    return {"status": "ok", "mode": MODE}


@app.get("/api/devices/")
async def devices():
    return await controller.get_all_device_statuses()


@app.post("/api/devices/{device_id}/state/")
async def device_state(device_id: int, request: StateRequest):
    try:
        return await controller.set_device_state(device_id, request.state)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/api/lighting/magenta/state/")
async def magenta_state(request: StateRequest):
    global magenta_off_since
    requested = request.state.upper().strip()
    if requested not in {"ON", "OFF"}:
        raise HTTPException(status_code=400, detail="state must be ON or OFF")
    try:
        result = await controller.set_magenta_state(requested)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if not result["success"]:
        raise HTTPException(status_code=503, detail="Grow-light state could not be confirmed")
    magenta_off_since = time.monotonic() if requested == "OFF" else None
    return {"success": True, "state": requested, "devices": result["devices"]}
