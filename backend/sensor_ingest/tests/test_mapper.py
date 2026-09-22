from django.test import SimpleTestCase

from sensor_ingest.services.mapper import (
    REQUIRED_SENSOR_SLUGS,
    normalize_payloads,
)
from telemetry.models import ObservationQuality


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


class LocalSensorMapperTests(SimpleTestCase):
    def test_normalizes_all_seven_physical_sensors(self):
        batch = normalize_payloads(WATER, AMBIENT)
        self.assertEqual(set(batch.sensor_values), set(REQUIRED_SENSOR_SLUGS))
        self.assertEqual(batch.missing_sensors, ())
        self.assertEqual(batch.invalid_sensors, ())
        self.assertTrue(
            all(
                value.quality_status == ObservationQuality.VALID
                for value in batch.sensor_values.values()
            )
        )

    def test_hardware_invalid_flag_skips_reading(self):
        water = {**WATER, "ph_valid": False}
        batch = normalize_payloads(water, AMBIENT)
        self.assertNotIn("water_ph", batch.sensor_values)
        self.assertIn("water_ph", batch.invalid_sensors)

    def test_physical_domain_violation_is_retained_as_suspect(self):
        water = {**WATER, "ph": 15}
        batch = normalize_payloads(water, AMBIENT)
        self.assertEqual(
            batch.sensor_values["water_ph"].quality_status,
            ObservationQuality.SUSPECT,
        )
