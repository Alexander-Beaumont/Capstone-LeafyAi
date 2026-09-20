from datetime import time

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from telemetry.models import Camera, Farm, FarmDevice, FarmLevel


class CameraFunctionApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="camera-api-test",
            password="test-password-123",
        )
        self.client.force_authenticate(self.user)

        farm = Farm.objects.create(name="Test Farm", location="Lab")
        device = FarmDevice.objects.create(
            farm=farm,
            name="Test Rack",
            device_type="rack",
        )
        self.level = FarmLevel.objects.create(device=device, level_number=1)
        self.camera = Camera.objects.create(
            farm_level=self.level,
            name="Lab Camera",
            source_type="RTSP",
            ip_address="192.168.1.106",
            rtsp_port=554,
            rtsp_path="/stream1",
            enabled=True,
            capture_interval_minutes=30,
            active_start_time=None,
            active_end_time=None,
        )

    def test_list_camera_api_is_explicit_function_view(self):
        response = self.client.get(reverse("camera-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.camera.id)

    def test_patch_camera_keeps_existing_public_contract(self):
        response = self.client.patch(
            reverse("camera-detail", kwargs={"camera_id": self.camera.id}),
            {"capture_interval_minutes": 15},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.camera.refresh_from_db()
        self.assertEqual(self.camera.capture_interval_minutes, 15)

    def test_patch_archive_hides_camera_from_list(self):
        response = self.client.patch(
            reverse("camera-detail", kwargs={"camera_id": self.camera.id}),
            {"is_archived": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.camera.refresh_from_db()
        self.assertTrue(self.camera.is_archived)
        self.assertFalse(self.camera.enabled)

        list_response = self.client.get(reverse("camera-list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data, [])

    def test_hard_delete_is_disabled(self):
        response = self.client.delete(
            reverse("camera-detail", kwargs={"camera_id": self.camera.id})
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Camera.objects.filter(pk=self.camera.id).exists())

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("camera-list"))
        self.assertIn(response.status_code, {401, 403})
