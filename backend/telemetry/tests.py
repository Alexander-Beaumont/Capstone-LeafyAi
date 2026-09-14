from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import Camera, Farm, FarmDevice, FarmLevel, Sensor, SensorReading


class TelemetryModelTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Test Device")
        self.test_sensor = Sensor.objects.create(
            device=device,
            sensor_type="pH Sensor",
            unit="pH",
        )

    def test_sensor_reading_creation(self):
        reading = SensorReading.objects.create(
            sensor=self.test_sensor,
            value=6.75,
        )

        saved_reading = SensorReading.objects.get(id=reading.id)
        self.assertEqual(saved_reading.sensor, self.test_sensor)
        self.assertEqual(saved_reading.value, 6.75)


class SensorAPIIntegrationTests(APITestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Test Device")
        self.sensor = Sensor.objects.create(
            device=device,
            sensor_type="EC Sensor",
            unit="uS/cm",
        )
        self.user = User.objects.create_user(username="telemetry-user", password="test-password")
        self.client.force_authenticate(user=self.user)

    def test_sensor_can_post_new_reading(self):
        response = self.client.post(
            "/api/sensor-readings/",
            {"sensor": self.sensor.id, "value": "1450.5"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SensorReading.objects.count(), 1)
        self.assertEqual(SensorReading.objects.first().value, 1450.5)


class CameraLifecycleAPITests(APITestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Camera Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Rack 1")
        self.level = FarmLevel.objects.create(device=device, level_number=1)
        self.user = User.objects.create_user(username="camera-user", password="test-password")
        self.client.force_authenticate(user=self.user)
        self.camera = Camera.objects.create(
            farm_level=self.level,
            name="Lifecycle Camera",
            position="Growth Area A",
            source_type="RTSP",
            ip_address="192.168.1.50",
            rtsp_port=554,
            rtsp_path="/stream1",
            enabled=True,
            cv_enabled=True,
            capture_interval_minutes=1,
        )

    def test_capture_interval_can_be_changed_without_recreating_camera(self):
        response = self.client.patch(
            f"/api/cameras/{self.camera.id}/",
            {"capture_interval_minutes": 30},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.camera.refresh_from_db()
        self.assertEqual(self.camera.capture_interval_minutes, 30)
        self.assertFalse(self.camera.is_archived)

    def test_archive_disables_camera_and_hides_it_from_active_list(self):
        response = self.client.patch(
            f"/api/cameras/{self.camera.id}/",
            {"is_archived": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.camera.refresh_from_db()
        self.assertTrue(self.camera.is_archived)
        self.assertFalse(self.camera.enabled)
        self.assertFalse(self.camera.cv_enabled)

        list_response = self.client.get("/api/cameras/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.camera.id, [row["id"] for row in list_response.data])

        # Direct detail remains readable for history/admin workflows.
        detail_response = self.client.get(f"/api/cameras/{self.camera.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertTrue(detail_response.data["is_archived"])

    def test_hard_delete_is_rejected(self):
        response = self.client.delete(f"/api/cameras/{self.camera.id}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Camera.objects.filter(id=self.camera.id).exists())

    def test_camera_api_uses_locked_farm_level_id_field_for_write_and_read(self):
        response = self.client.post(
            "/api/cameras/",
            {
                "farm_level_id": self.level.id,
                "name": "API Field Camera",
                "position": "Growth Area B",
                "source_type": "WEBCAM",
                "webcam_index": 0,
                "enabled": True,
                "cv_enabled": True,
                "capture_interval_minutes": 30,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["farm_level_id"], self.level.id)
        self.assertNotIn("farm_level", response.data)


class FreshInstallCameraTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fresh-user", password="test-password")
        self.client.force_authenticate(user=self.user)

    def test_camera_collection_is_empty_until_user_adds_camera(self):
        response = self.client.get("/api/cameras/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), [])
