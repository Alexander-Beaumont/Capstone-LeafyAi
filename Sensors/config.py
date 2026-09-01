DJANGO_API_URL = "http://127.0.0.1:8000/api/telemetry/sensor-readings/"
WATER_QUALITY_URL = "http://192.168.1.100/readings"
AMBIENT_SENSOR_URL = "http://leafy-ai.local:8080/readings"

SENSOR_IDS = {
    "ph": 1,
    "ec": 2,
    "water_temp": 3,
    "ambient_temp": 4,
    "humidity": 5,
    "dew_point": 6,
    "water_level": 7
}

POLLING_INTERVAL_SECONDS = 10