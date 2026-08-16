import requests
import time
from datetime import datetime

# The URL of your new Django backend endpoint 
# (You will need to update this to match the actual path in your urls.py)
DJANGO_API_URL = "http://127.0.0.1:8000/api/telemetry/sensor-readings/"

while True:
    try:
        # Fetch data from the physical sensors
        response = requests.get("http://192.168.1.100/readings", timeout=5)
        response.raise_for_status()
        data = response.json()

        current_time = datetime.now().isoformat()

        # Check if the readings are valid
        if data["ph_valid"] and data["ec_valid"] and data["water_temperature_valid"]:
            
            # 1. Package the extracted data into a dictionary
            payload = {
                "time": current_time,
                "ph": data["ph"],
                "ec": data["ec"],
                "water_temp": data["water_temperature_c"]
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