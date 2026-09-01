import requests

class DjangoBackend:
    def __init__(self, api_url, sensor_ids):
        self.api_url = api_url
        self.sensor_ids = sensor_ids

    def map_data(self, water_data, ambient_data):
        return [
            {"sensor": self.sensor_ids["ph"], "value": water_data["ph"]},
            {"sensor": self.sensor_ids["ec"], "value": water_data["ec"]},
            {"sensor": self.sensor_ids["water_temp"], "value": water_data["water_temperature_c"]},
            {"sensor": self.sensor_ids["ambient_temp"], "value": ambient_data["ambient_temperature_c"]},
            {"sensor": self.sensor_ids["humidity"], "value": ambient_data["humidity_percent"]},
            {"sensor": self.sensor_ids["dew_point"], "value": ambient_data["dew_point_c"]},
            {"sensor": self.sensor_ids["water_level"], "value": ambient_data["water_level"]}
        ]

    def send_readings(self, readings):
        print("Sending new batch of readings to backend...")
        for payload in readings:
            try:
                resp = requests.post(self.api_url, json=payload, timeout=5)
                if resp.status_code in [200, 201]:
                    print(f"  -> Successfully saved Sensor {payload['sensor']}: {payload['value']}")
                else:
                    print(f"  -> Failed to save Sensor {payload['sensor']}. Error: {resp.text}")
            except requests.exceptions.RequestException as e:
                print(f"  -> HTTP Error sending Sensor {payload['sensor']}: {e}")
        print("-" * 30)