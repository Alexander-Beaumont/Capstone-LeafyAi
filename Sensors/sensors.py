import requests

class SensorReader:
    def __init__(self, water_url, ambient_url):
        self.water_url = water_url
        self.ambient_url = ambient_url

    def fetch_readings(self):
        water_resp = requests.get(self.water_url, timeout=5)
        water_resp.raise_for_status()
        
        ambient_resp = requests.get(self.ambient_url, timeout=5)
        ambient_resp.raise_for_status()
        
        return water_resp.json(), ambient_resp.json()
        
    def is_valid(self, water_data, ambient_data):
        water_valid = (
            water_data.get("ph_valid") and 
            water_data.get("ec_valid") and 
            water_data.get("water_temperature_valid")
        )
        ambient_valid = (
            ambient_data.get("ambient_valid") and 
            ambient_data.get("water_level_valid")
        )
        return water_valid and ambient_valid