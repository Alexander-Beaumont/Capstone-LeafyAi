from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import Camera, Farm, FarmDevice, Sensor, SensorReading


class TelemetryModelTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Test Farm")
        self.device = FarmDevice.objects.create(farm=farm, name="Test Device")
        self.test_sensor = Sensor.objects.create(
            device=self.device,
            sensor_type="ph",
            slug="water-ph",
            unit="pH",
        )

    def test_machine_slugs_are_stable_and_auto_generated_when_omitted(self):
        self.assertEqual(self.device.slug, "test-device")
        sensor = Sensor.objects.create(
            device=self.device,
            sensor_type="ambient_temperature",
            unit="°C",
        )
        self.assertEqual(sensor.slug, "ambient_temperature")

    def test_sensor_reading_preserves_measurement_and_receipt_times(self):
        measured_at = timezone.now()
        reading = SensorReading.objects.create(
            sensor=self.test_sensor,
            value=Decimal("6.7500"),
            measured_at=measured_at,
            source="local_http",
            source_channel_id="channel",
            source_entry_id=10,
        )
        saved = SensorReading.objects.get(id=reading.id)
        self.assertEqual(saved.sensor, self.test_sensor)
        self.assertEqual(saved.value, Decimal("6.7500"))
        self.assertEqual(saved.measured_at, measured_at)
        self.assertIsNotNone(saved.received_at)


class BootstrapLeafyTests(TestCase):
    def test_bootstrap_creates_and_updates_the_configured_camera(self):
        call_command("bootstrap_leafy")
        call_command("bootstrap_leafy")

        self.assertEqual(Camera.objects.count(), 1)


class SensorAPIIntegrationTests(APITestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Test Device")
        self.sensor = Sensor.objects.create(
            device=device,
            sensor_type="ec",
            slug="electrical-conductivity",
            unit="µS/cm",
        )
        self.reading = SensorReading.objects.create(
            sensor=self.sensor,
            value=Decimal("1450.5000"),
            measured_at=timezone.now(),
        )
        self.user = User.objects.create_user(
            username="telemetry-user",
            password="test-password",
        )
        self.client.force_authenticate(user=self.user)

    def test_sensor_reading_api_is_read_only(self):
        response = self.client.post(
            "/api/sensor-readings/",
            {"sensor": self.sensor.id, "value": "1500"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(SensorReading.objects.count(), 1)

    def test_sensor_reading_api_exposes_provenance(self):
        response = self.client.get(f"/api/sensor-readings/{self.reading.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sensor_slug"], "electrical-conductivity")
        self.assertIn("measured_at", response.data)
        self.assertIn("received_at", response.data)
        self.assertIn("quality_status", response.data)
