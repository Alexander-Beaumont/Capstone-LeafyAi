import requests
import time

DJANGO_API_URL = "http://127.0.0.1:8000/api/sensor-readings/"

# Updated URLs based on your screenshots
WATER_QUALITY_URL = "http://watersensors.local/readings"
AMBIENT_SENSOR_URL = "http://Leafy-AI.local:8080/readings"

# UPDATE THESE NUMBERS based on the primary keys of the 'Sensors' in your Django database
SENSOR_IDS = {
    "ph": 1,
    "ec": 2,
    "water_temp": 3,
    "ambient_temp": 4,
    "humidity": 5,
    "dew_point": 6,
    "water_level": 7
}

while True:
    readings_to_send = []

    try:
        # 1. Fetch data from Water Sensors
        try:
            water_resp = requests.get(WATER_QUALITY_URL, timeout=5)
            water_resp.raise_for_status()
            water_data = water_resp.json()

            # Check if water readings are valid
            if water_data.get("ph_valid") and water_data.get("ec_valid") and water_data.get("water_temperature_valid"):
                readings_to_send.extend([
                    {"sensor": SENSOR_IDS["ph"], "value": water_data["ph"]},
                    {"sensor": SENSOR_IDS["ec"], "value": water_data["ec"]},
                    {"sensor": SENSOR_IDS["water_temp"], "value": water_data["water_temperature_c"]},
                ])
        except Exception as e:
            print(f"Warning: Could not fetch Water Quality data. ({e})")

        # 2. Fetch data from Ambient Sensors
        try:
            ambient_resp = requests.get(AMBIENT_SENSOR_URL, timeout=5)
            ambient_resp.raise_for_status()
            ambient_data = ambient_resp.json()

            # Check if ambient readings are valid
            if ambient_data.get("ambient_valid") and ambient_data.get("water_level_valid"):
                readings_to_send.extend([
                    {"sensor": SENSOR_IDS["ambient_temp"], "value": ambient_data["ambient_temperature_c"]},
                    {"sensor": SENSOR_IDS["humidity"], "value": ambient_data["humidity_percent"]},
                    {"sensor": SENSOR_IDS["dew_point"], "value": ambient_data["dew_point_c"]},
                    {"sensor": SENSOR_IDS["water_level"], "value": ambient_data["water_level"]}
                ])
        except Exception as e:
            print(f"Warning: Could not fetch Ambient Sensor data. ({e})")

        # 3. Post whatever valid readings we collected to Django
        if readings_to_send:
            print(f"Sending {len(readings_to_send)} readings to backend...")
            for payload in readings_to_send:
                post_response = requests.post(DJANGO_API_URL, json=payload)
                
                if post_response.status_code in [200, 201]:
                    print(f"  -> Successfully saved Sensor {payload['sensor']}: {payload['value']}")
                else:
                    print(f"  -> Failed to save Sensor {payload['sensor']}. Error: {post_response.text}")
            print("-" * 30)
        else:
            print("No valid readings collected this cycle. Waiting to retry...")
            print("-" * 30)

    except Exception as e:
        print(f"Unexpected error in main loop: {e}")

    # Wait 10 seconds before polling the sensors again
    time.sleep(10)