"""Environment-backed runtime settings for the LeafyAI hardware sensor worker."""
from __future__ import annotations

import os

BACKEND_BASE_URL = os.getenv("LEAFY_BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
DJANGO_API_URL = f"{BACKEND_BASE_URL}/api/sensor-readings/"
BACKEND_USERNAME = os.getenv("LEAFY_BACKEND_USERNAME", os.getenv("LEAFY_MVP_USERNAME", ""))
BACKEND_PASSWORD = os.getenv("LEAFY_BACKEND_PASSWORD", os.getenv("LEAFY_MVP_PASSWORD", ""))
BACKEND_ACCESS_TOKEN = os.getenv("LEAFY_BACKEND_ACCESS_TOKEN", "")
BACKEND_REFRESH_TOKEN = os.getenv("LEAFY_BACKEND_REFRESH_TOKEN", "")

WATER_QUALITY_URL = os.getenv("LEAFY_WATER_QUALITY_URL", "http://192.168.1.100/readings")
AMBIENT_SENSOR_URL = os.getenv("LEAFY_AMBIENT_SENSOR_URL", "http://192.168.1.111:8080/readings")
POLLING_INTERVAL_SECONDS = float(os.getenv("LEAFY_SENSOR_POLL_SECONDS", "10"))
HTTP_TIMEOUT_SECONDS = float(os.getenv("LEAFY_SENSOR_HTTP_TIMEOUT", "5"))

# Stable API identities. Numeric DB IDs are discovered from GET /api/sensors/.
SENSOR_TYPES = {
    "ph": "ph",
    "ec": "ec",
    "water_temp": "water_temp",
    "ambient_temp": "ambient_temp",
    "humidity": "humidity",
    "dew_point": "dew_point",
    "water_level": "water_level",
}
