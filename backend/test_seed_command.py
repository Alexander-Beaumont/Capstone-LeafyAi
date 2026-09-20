from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from sensor_ingest.services.mapper import REQUIRED_SENSOR_SLUGS
from telemetry.models import Farm, FarmDevice, Sensor


@override_settings(
    SENSOR_INGEST_DEVICE_SLUG="leafy-pi",
    SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS=30,
    SENSOR_INGEST_SENSOR_STALE_SECONDS=120,
)
class SeedSensorsCommandTests(TestCase):
    def test_seed_command_is_repeatable(self):
        farm = Farm.objects.create(name="Farm")
        FarmDevice.objects.create(farm=farm, name="Leafy Pi", slug="leafy-pi")
        output = StringIO()
        call_command("seed_sensors", stdout=output)
        call_command("seed_sensors", stdout=output)
        self.assertEqual(Sensor.objects.count(), len(REQUIRED_SENSOR_SLUGS))
        self.assertEqual(
            set(Sensor.objects.values_list("slug", flat=True)),
            set(REQUIRED_SENSOR_SLUGS),
        )
