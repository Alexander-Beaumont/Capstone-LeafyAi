import requests
import time
from datetime import datetime

# The URL of your new Django backend endpoint 
# (You will need to update this to match the actual path in your urls.py)
DJANGO_API_URL = "http://127.0.0.1:8000/api/telemetry/sensor-readings/"

WATER_QUALITY_URL = "http://192.168.1.100/readings"
AMBIENT_SENSOR_URL = "http://leafy-ai.local:8080/readings"

while True:
    try:
        current_time = datetime.now().isoformat()
        
        # 1. Fetch data from the original water quality sensors
        water_resp = requests.get(WATER_QUALITY_URL, timeout=5)
        water_resp.raise_for_status()
        water_data = water_resp.json()

        # 2. Fetch data from the new ambient & level sensors
        ambient_resp = requests.get(AMBIENT_SENSOR_URL, timeout=5)
        ambient_resp.raise_for_status()
        ambient_data = ambient_resp.json()

        # Check if the readings are valid
        water_valid = water_data.get("ph_valid") and water_data.get("ec_valid") and water_data.get("water_temperature_valid")
        ambient_valid = ambient_data.get("ambient_valid") and ambient_data.get("water_level_valid")

        if water_valid and ambient_valid:
            
            # 4. Package the extracted data into a single payload
            payload = {
                "time": current_time,
                # Water Quality Data
                "ph": water_data["ph"],
                "ec": water_data["ec"],
                "water_temp": water_data["water_temperature_c"],
                # New Ambient & Level Data
                "ambient_temp": ambient_data["ambient_temperature_c"],
                "humidity": ambient_data["humidity_percent"],
                "dew_point": ambient_data["dew_point_c"],
                "water_level": ambient_data["water_level"]
            }
            
            print(f"[{current_time}] Sending data to backend: {payload}")
            
            # 2. Send the data to the Django backend via POST
            post_response = requests.post(DJANGO_API_URL, json=payload)
            
            if post_response.status_code in [200, 201]:
                print("Successfully saved to backend!")
            else:
                print(f"Failed to save. Backend responded with: {post_response.status_code} - {post_response.text}")

        else:
            print(f"[{current_time}] Invalid reading received from sensor.")

    except Exception as e:
        print(f"Network or connection error: {e}")

    time.sleep(10)