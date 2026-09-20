from django.test import TestCase, override_settings

from sensor_ingest.exceptions import IngestionConfigurationError
from sensor_ingest.models import IngestionRecord, IngestionSourceState
from sensor_ingest.services.collector import SensorCollector
from sensor_ingest.services.mapper import SENSOR_DEFINITIONS
from sensor_ingest.tests.fixtures import VALID_ENTRY, make_entry
from telemetry.models import Farm, FarmDevice, Sensor, SensorReading


class FakeClient:
    def __init__(self, *, latest=None, recent=None):
        self.latest = latest or VALID_ENTRY
        self.recent = recent or []
        self.latest_calls = 0
        self.recent_calls = 0

    def get_latest(self):
        self.latest_calls += 1
        return self.latest

    def get_recent(self, *, results):
        self.recent_calls += 1
        return self.recent[-results:]


@override_settings(
    THINGSPEAK_CHANNEL_ID="3464601",
    THINGSPEAK_READ_API_KEY="test-read-key",
    SENSOR_INGEST_DEVICE_SLUG="leafy-pi",
    SENSOR_INGEST_SOURCE_KEY="thingspeak-primary",
)
class SensorCollectorTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Farm")
        self.device = FarmDevice.objects.create(
            farm=farm,
            name="Leafy Pi",
            slug="leafy-pi",
        )
        for definition in SENSOR_DEFINITIONS:
            Sensor.objects.create(
                device=self.device,
                slug=definition.slug,
                sensor_type=definition.sensor_type,
                unit=definition.unit,
            )

    def test_collect_latest_updates_source_health_and_is_idempotent(self):
        fake = FakeClient(latest=VALID_ENTRY)
        collector = SensorCollector(client=fake)
        first = collector.collect_latest()
        second = collector.collect_latest()

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(SensorReading.objects.count(), 6)
        source = IngestionSourceState.objects.get(pk="thingspeak-primary")
        self.assertEqual(source.last_source_entry_id, 12345)
        self.assertEqual(source.consecutive_failures, 0)
        self.assertIsNotNone(source.last_http_success_at)

    def test_reconcile_backfills_missing_entries_without_duplication(self):
        history = [
            make_entry(1, "2026-09-06T10:00:00Z"),
            make_entry(2, "2026-09-06T10:01:00Z"),
            make_entry(3, "2026-09-06T10:02:00Z"),
        ]
        collector = SensorCollector(client=FakeClient(recent=history))
        first = collector.reconcile(results=100)
        second = collector.reconcile(results=100)
        self.assertEqual(first["created"], 3)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["duplicates"], 3)
        self.assertEqual(IngestionRecord.objects.count(), 3)
        self.assertEqual(SensorReading.objects.count(), 18)

    def test_configuration_fails_clearly_when_sensor_missing(self):
        Sensor.objects.filter(slug="water_ph").delete()
        collector = SensorCollector(client=FakeClient())
        with self.assertRaises(IngestionConfigurationError):
            collector.validate_configuration()
