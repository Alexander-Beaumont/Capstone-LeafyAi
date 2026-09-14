from __future__ import annotations

import time

from backend_api import DjangoBackend
from config import (
    AMBIENT_SENSOR_URL,
    BACKEND_ACCESS_TOKEN,
    BACKEND_BASE_URL,
    BACKEND_PASSWORD,
    BACKEND_REFRESH_TOKEN,
    BACKEND_USERNAME,
    HTTP_TIMEOUT_SECONDS,
    POLLING_INTERVAL_SECONDS,
    SENSOR_TYPES,
    WATER_QUALITY_URL,
)
from sensors import SensorReader


class TelemetryController:
    def __init__(self):
        self.sensor_reader = SensorReader(
            WATER_QUALITY_URL,
            AMBIENT_SENSOR_URL,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        self.backend = DjangoBackend(
            BACKEND_BASE_URL,
            SENSOR_TYPES,
            username=BACKEND_USERNAME,
            password=BACKEND_PASSWORD,
            access_token=BACKEND_ACCESS_TOKEN,
            refresh_token=BACKEND_REFRESH_TOKEN,
            timeout=HTTP_TIMEOUT_SECONDS,
        )

    def run(self):
        print("LeafyAI Sensor worker started (synthetic readings disabled).")
        print(f"Water-quality endpoint: {WATER_QUALITY_URL}")
        print(f"Ambient endpoint: {AMBIENT_SENSOR_URL}")
        while True:
            if not WATER_QUALITY_URL or not AMBIENT_SENSOR_URL:
                print("Sensor hardware not configured; waiting for LEAFY_WATER_QUALITY_URL and LEAFY_AMBIENT_SENSOR_URL.")
                time.sleep(max(5.0, POLLING_INTERVAL_SECONDS))
                continue
            try:
                water_data, ambient_data = self.sensor_reader.fetch_readings()
                if self.sensor_reader.is_valid(water_data, ambient_data):
                    readings = self.backend.map_data(water_data, ambient_data)
                    self.backend.send_readings(readings)
                else:
                    print("Invalid sensor reading; batch not uploaded.")
            except Exception as exc:
                print(f"Sensor worker warning: {exc}")
            time.sleep(max(1.0, POLLING_INTERVAL_SECONDS))


if __name__ == "__main__":
    TelemetryController().run()
