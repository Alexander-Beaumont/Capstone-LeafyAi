from django.test import TestCase, override_settings

from sensor_ingest.services.collector import SensorCollector
from sensor_ingest.services.mapper import SENSOR_DEFINITIONS
from telemetry.models import Farm, FarmDevice, Sensor, SensorReading


WATER_URL = "http://192.168.1.100/readings"
AMBIENT_URL = "http://192.168.1.111:8080/readings"

WATER = {
    "ph": 6.375,
    "ec": 2987.0,
    "water_temperature_c": 23.757,
    "ph_valid": True,
    "ec_valid": True,
    "water_temperature_valid": True,
}

AMBIENT = {
    "ambient_temperature_c": 23.48,
    "humidity_percent": 47.4,
    "dew_point_c": 11.65,
    "water_level": 11.1,
    "ambient_valid": True,
    "water_level_valid": True,
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        if url == WATER_URL:
            return FakeResponse(WATER)
        if url == AMBIENT_URL:
            return FakeResponse(AMBIENT)
        raise AssertionError(f"Unexpected URL: {url}")


@override_settings(
    LEAFY_WATER_QUALITY_URL=WATER_URL,
    LEAFY_AMBIENT_SENSOR_URL=AMBIENT_URL,
    SENSOR_INGEST_DEVICE_SLUG="test-device",
    SENSOR_INGEST_HTTP_TIMEOUT_SECONDS=5,
    SENSOR_INGEST_HTTP_RETRY_TOTAL=0,
    SENSOR_INGEST_HTTP_RETRY_BACKOFF=0,
)
class LocalSensorCollectorTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Farm")
        self.device = FarmDevice.objects.create(
            farm=farm,
            name="LeafyAI",
            slug="test-device",
        )
        for definition in SENSOR_DEFINITIONS:
            Sensor.objects.create(
                device=self.device,
                slug=definition.slug,
                sensor_type=definition.sensor_type,
                unit=definition.unit,
                enabled=True,
            )

    def test_collect_latest_stores_seven_local_readings(self):
        session = FakeSession()
        count = SensorCollector(session=session).collect_latest()

        self.assertEqual(count, 7)
        self.assertEqual(SensorReading.objects.count(), 7)
        self.assertEqual(
            set(SensorReading.objects.values_list("source", flat=True)),
            {"local_http"},
        )
        self.assertEqual(
            set(SensorReading.objects.values_list("source_channel_id", flat=True)),
            {"water_quality", "ambient"},
        )
        self.assertEqual(
            session.calls,
            [(WATER_URL, 5), (AMBIENT_URL, 5)],
        )
