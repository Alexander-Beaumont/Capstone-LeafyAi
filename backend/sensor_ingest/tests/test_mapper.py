from decimal import Decimal

from django.test import SimpleTestCase

from sensor_ingest.services.mapper import normalize_entry
from sensor_ingest.services.parser import parse_entry
from sensor_ingest.tests.fixtures import VALID_ENTRY
from telemetry.models import ObservationQuality


class ThingSpeakMapperTests(SimpleTestCase):
    def test_all_eight_fields_are_semantically_separated(self):
        snapshot = normalize_entry(parse_entry(VALID_ENTRY))
        self.assertEqual(len(snapshot.sensor_values), 6)
        self.assertEqual(snapshot.sensor_values["water_ph"].value, Decimal("6.12"))
        self.assertEqual(snapshot.irrigation_pump_state, "on")
        self.assertEqual(snapshot.target_ec.value, Decimal("1500"))
        self.assertEqual(snapshot.missing_fields, ())
        self.assertEqual(snapshot.invalid_fields, ())

    def test_missing_one_sensor_does_not_discard_other_values(self):
        payload = dict(VALID_ENTRY, field1=None)
        snapshot = normalize_entry(parse_entry(payload))
        self.assertNotIn("water_ph", snapshot.sensor_values)
        self.assertIn("electrical_conductivity", snapshot.sensor_values)
        self.assertIn("field1", snapshot.missing_fields)

    def test_non_numeric_sensor_is_isolated_as_invalid(self):
        payload = dict(VALID_ENTRY, field2="not-a-number")
        snapshot = normalize_entry(parse_entry(payload))
        self.assertNotIn("electrical_conductivity", snapshot.sensor_values)
        self.assertIn("field2", snapshot.invalid_fields)
        self.assertIn("water_ph", snapshot.sensor_values)

    def test_physically_impossible_ph_is_stored_as_suspect(self):
        payload = dict(VALID_ENTRY, field1="15.2")
        snapshot = normalize_entry(parse_entry(payload))
        ph = snapshot.sensor_values["water_ph"]
        self.assertEqual(ph.value, Decimal("15.2"))
        self.assertEqual(ph.quality_status, ObservationQuality.SUSPECT)
        self.assertIn("0-14", ph.quality_notes)

    def test_pump_state_accepts_numeric_one_point_zero(self):
        payload = dict(VALID_ENTRY, field7="1.0")
        snapshot = normalize_entry(parse_entry(payload))
        self.assertEqual(snapshot.irrigation_pump_state, "on")

    def test_pump_state_must_be_zero_or_one(self):
        payload = dict(VALID_ENTRY, field7="7")
        snapshot = normalize_entry(parse_entry(payload))
        self.assertIsNone(snapshot.irrigation_pump_state)
        self.assertIn("field7", snapshot.invalid_fields)
