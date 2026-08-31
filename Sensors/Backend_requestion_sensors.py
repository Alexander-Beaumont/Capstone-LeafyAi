import requests
import time

DJANGO_API_URL = "http://127.0.0.1:8000/api/telemetry/sensor-readings/"
WATER_QUALITY_URL = "http://192.168.1.100/readings"
AMBIENT_SENSOR_URL = "http://leafy-ai.local:8080/readings"

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
    try:
        # 1. Fetch data from the sensors
        water_resp = requests.get(WATER_QUALITY_URL, timeout=5)
        water_resp.raise_for_status()
        water_data = water_resp.json()

        ambient_resp = requests.get(AMBIENT_SENSOR_URL, timeout=5)
        ambient_resp.raise_for_status()
        ambient_data = ambient_resp.json()

        # 2. Check if the readings are valid
        water_valid = water_data.get("ph_valid") and water_data.get("ec_valid") and water_data.get("water_temperature_valid")
        ambient_valid = ambient_data.get("ambient_valid") and ambient_data.get("water_level_valid")

        if water_valid and ambient_valid:
            
            # 3. Map the collected data to their respective Sensor IDs
            readings_to_send = [
                {"sensor": SENSOR_IDS["ph"], "value": water_data["ph"]},
                {"sensor": SENSOR_IDS["ec"], "value": water_data["ec"]},
                {"sensor": SENSOR_IDS["water_temp"], "value": water_data["water_temperature_c"]},
                {"sensor": SENSOR_IDS["ambient_temp"], "value": ambient_data["ambient_temperature_c"]},
                {"sensor": SENSOR_IDS["humidity"], "value": ambient_data["humidity_percent"]},
                {"sensor": SENSOR_IDS["dew_point"], "value": ambient_data["dew_point_c"]},
                {"sensor": SENSOR_IDS["water_level"], "value": ambient_data["water_level"]}
            ]
            
            # 4. Loop through and POST each reading to the backend
            print("Sending new batch of readings to backend...")
            for payload in readings_to_send:
                post_response = requests.post(DJANGO_API_URL, json=payload)
                
                if post_response.status_code in [200, 201]:
                    print(f"  -> Successfully saved Sensor {payload['sensor']}: {payload['value']}")
                else:
                    print(f"  -> Failed to save Sensor {payload['sensor']}. Error: {post_response.text}")
            print("-" * 30)

        else:
            print("Invalid reading received from sensor.")

    except Exception as e:
        print(f"Network or connection error: {e}")

    time.sleep(10)