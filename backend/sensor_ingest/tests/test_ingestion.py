from decimal import Decimal

from django.test import TestCase

from sensor_ingest.exceptions import IngestionConflictError
from sensor_ingest.models import IngestionRecord, IngestionSourceState
from sensor_ingest.services.ingestion import ingest_snapshot
from sensor_ingest.services.mapper import SENSOR_DEFINITIONS, normalize_entry
from sensor_ingest.services.parser import parse_entry
from sensor_ingest.tests.fixtures import VALID_ENTRY, make_entry
from telemetry.models import (
    ActuatorStateObservation,
    Farm,
    FarmDevice,
    Sensor,
    SensorReading,
    SetpointObservation,
)


class SensorIngestionTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Test Farm")
        self.device = FarmDevice.objects.create(
            farm=farm,
            name="Pi Farm Device",
            slug="pi-farm",
        )
        for definition in SENSOR_DEFINITIONS:
            Sensor.objects.create(
                device=self.device,
                slug=definition.slug,
                sensor_type=definition.sensor_type,
                unit=definition.unit,
                expected_interval_seconds=30,
                stale_after_seconds=120,
            )
        self.source = IngestionSourceState.objects.create(
            key="thingspeak-primary",
            provider="thingspeak",
            external_source_id="3464601",
        )

    def _ingest(self, payload):
        snapshot = normalize_entry(parse_entry(payload))
        return ingest_snapshot(
            source_state=self.source,
            device=self.device,
            snapshot=snapshot,
        )

    def test_complete_entry_creates_all_observation_types(self):
        result = self._ingest(VALID_ENTRY)
        self.assertTrue(result.created)
        self.assertEqual(result.status, IngestionRecord.Status.COMPLETE)
        self.assertEqual(SensorReading.objects.count(), 6)
        self.assertEqual(ActuatorStateObservation.objects.count(), 1)
        self.assertEqual(SetpointObservation.objects.count(), 1)
        self.assertEqual(IngestionRecord.objects.count(), 1)

        ph = SensorReading.objects.get(sensor__slug="water_ph")
        self.assertEqual(ph.value, Decimal("6.1200"))
        self.assertEqual(ph.source_entry_id, 12345)
        self.assertEqual(ph.source, "thingspeak")

    def test_same_source_entry_is_idempotent(self):
        first = self._ingest(VALID_ENTRY)
        second = self._ingest(VALID_ENTRY)
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertTrue(second.duplicate)
        self.assertEqual(SensorReading.objects.count(), 6)
        self.assertEqual(IngestionRecord.objects.count(), 1)

    def test_reused_entry_id_with_changed_payload_is_conflict(self):
        self._ingest(VALID_ENTRY)
        changed = dict(VALID_ENTRY, field1="8.5")
        with self.assertRaises(IngestionConflictError):
            self._ingest(changed)
        self.assertEqual(
            SensorReading.objects.get(sensor__slug="water_ph").value,
            Decimal("6.1200"),
        )

    def test_missing_field_produces_partial_record_without_losing_others(self):
        result = self._ingest(dict(VALID_ENTRY, field1=None))
        self.assertEqual(result.status, IngestionRecord.Status.PARTIAL)
        self.assertEqual(SensorReading.objects.count(), 5)
        self.assertFalse(
            SensorReading.objects.filter(sensor__slug="water_ph").exists()
        )
        self.assertTrue(
            SensorReading.objects.filter(
                sensor__slug="electrical_conductivity"
            ).exists()
        )

    def test_out_of_order_entries_keep_source_measurement_times(self):
        later = make_entry(200, "2026-09-06T10:35:00Z")
        earlier = make_entry(199, "2026-09-06T10:34:00Z")
        self._ingest(later)
        self._ingest(earlier)
        readings = list(
            SensorReading.objects.filter(sensor__slug="water_ph").order_by(
                "measured_at"
            )
        )
        self.assertLess(readings[0].measured_at, readings[1].measured_at)
