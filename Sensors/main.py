import time
from config import (
    DJANGO_API_URL, WATER_QUALITY_URL, AMBIENT_SENSOR_URL, 
    SENSOR_IDS, POLLING_INTERVAL_SECONDS
)
from sensors import SensorReader
from backend_api import DjangoBackend

class TelemetryController:
    def __init__(self):
        self.sensor_reader = SensorReader(WATER_QUALITY_URL, AMBIENT_SENSOR_URL)
        self.backend = DjangoBackend(DJANGO_API_URL, SENSOR_IDS)

    def run(self):
        print("Starting Telemetry Controller...")
        while True:
            try:
                water_data, ambient_data = self.sensor_reader.fetch_readings()

                if self.sensor_reader.is_valid(water_data, ambient_data):
                    readings_to_send = self.backend.map_data(water_data, ambient_data)
                    self.backend.send_readings(readings_to_send)
                else:
                    print("Invalid reading received from sensors.")

            except Exception as e:
                print(f"Network or connection error: {e}")

            time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    controller = TelemetryController()
    controller.run()