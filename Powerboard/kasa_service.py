import asyncio
from datetime import datetime
from kasa.iot import IotStrip
from config import POWERBOARDS, DEVICES

async def get_all_device_statuses():
    """
    Connects to the powerboards, retrieves the status of each socket,
    and returns a structured list of dictionaries.
    """
    strips = {}
    status_payload = []
    timestamp = datetime.utcnow().isoformat()

    # 1. Connect to all boards
    for board_name, config in POWERBOARDS.items():
        try:
            strip = IotStrip(config["ip"])
            await strip.update()
            strips[board_name] = strip
        except Exception as e:
            print(f"Warning: Could not connect to {board_name} at {config['ip']} - {e}")

    # 2. Extract specific socket statuses
    for device_id, device_info in DEVICES.items():
        board_name = device_info["board"]
        
        # Handle if the board went offline
        if board_name not in strips:
            status_payload.append({
                "device_id": device_id,
                "name": device_info["name"],
                "is_on": None,
                "status_text": "ERROR",
                "timestamp": timestamp
            })
            continue

        # Extract data from the active board
        strip = strips[board_name]
        plug = strip.children[device_info["child_index"]]
        
        status_payload.append({
            "device_id": device_id,
            "name": device_info["name"],
            "is_on": plug.is_on,
            "status_text": "ON" if plug.is_on else "OFF",
            "timestamp": timestamp
        })

    return status_payload