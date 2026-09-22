from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from farm_state.services import build_farm_state
from telemetry.models import Farm, FarmDevice, Sensor, SensorReading


@override_settings(FARM_STATE_SENSOR_TREND_WINDOW_MINUTES=30)
class FarmStateSensorTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Farm")
        self.device = FarmDevice.objects.create(
            farm=self.farm,
            name="Device",
            slug="device",
        )
        self.sensor = Sensor.objects.create(
            device=self.device,
            slug="electrical-conductivity",
            sensor_type="ec",
            unit="µS/cm",
            stale_after_seconds=120,
        )

    def test_state_uses_source_measurement_time_and_includes_trend(self):
        now = timezone.now()
        SensorReading.objects.create(
            sensor=self.sensor,
            value=Decimal("1500"),
            measured_at=now - timedelta(minutes=10),
            source="local_http",
            source_channel_id="channel",
            source_entry_id=1,
        )
        latest = SensorReading.objects.create(
            sensor=self.sensor,
            value=Decimal("1400"),
            measured_at=now - timedelta(seconds=30),
            source="local_http",
            source_channel_id="channel",
            source_entry_id=2,
        )

        state = build_farm_state(self.farm)
        sensor_state = state["devices"][0]["sensors"][0]
        self.assertEqual(sensor_state["source_entry_id"], 2)
        self.assertEqual(sensor_state["measured_at"], latest.measured_at.isoformat())
        self.assertEqual(sensor_state["status"], "fresh")
        self.assertEqual(sensor_state["trend"]["sample_count"], 2)
        self.assertEqual(sensor_state["trend"]["direction"], "falling")

    def test_sensor_specific_stale_threshold_is_used(self):
        SensorReading.objects.create(
            sensor=self.sensor,
            value=Decimal("1400"),
            measured_at=timezone.now() - timedelta(minutes=3),
        )
        state = build_farm_state(self.farm)
        sensor_state = state["devices"][0]["sensors"][0]
        self.assertEqual(sensor_state["status"], "stale")
