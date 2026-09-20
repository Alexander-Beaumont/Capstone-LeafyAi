from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import Camera, Farm, FarmDevice, FarmLevel, Sensor, SensorReading


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
            source="thingspeak",
            source_channel_id="channel",
            source_entry_id=10,
        )
        saved = SensorReading.objects.get(id=reading.id)
        self.assertEqual(saved.sensor, self.test_sensor)
        self.assertEqual(saved.value, Decimal("6.7500"))
        self.assertEqual(saved.measured_at, measured_at)
        self.assertIsNotNone(saved.received_at)


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


class RawCameraImageApiTests(APITestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.media_override = self.settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        user = User.objects.create_user(username="camera-user", password="password")
        self.client.force_authenticate(user)
        farm = Farm.objects.create(name="Farm")
        device = FarmDevice.objects.create(farm=farm, name="Device")
        level = FarmLevel.objects.create(device=device, level_number=1)
        self.camera = Camera.objects.create(farm_level=level, name="Camera", source_type="WEBCAM")

    def test_upload_and_get_latest_raw_image(self):
        image = SimpleUploadedFile("farm.jpg", b"raw-jpeg-data", content_type="image/jpeg")
        uploaded = self.client.post(
            f"/api/cameras/{self.camera.id}/official-image/",
            {"image": image},
            format="multipart",
        )
        self.assertEqual(uploaded.status_code, status.HTTP_201_CREATED)
        latest = self.client.get(f"/api/cameras/{self.camera.id}/latest-image/")
        self.assertEqual(latest.status_code, status.HTTP_200_OK)
        self.assertEqual(latest.data["image_id"], uploaded.data["image_id"])
