from datetime import datetime, timezone

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from telemetry.models import Camera, CameraImage, Farm, FarmDevice, FarmLevel
from cv.models import ImageAnalysis


class WholeImageCVApiTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Device")
        level = FarmLevel.objects.create(device=device, level_number=1)
        self.camera = Camera.objects.create(farm_level=level, name="Camera", source_type="WEBCAM")
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(username="tester"))

    def test_official_image_and_aggregate_ingest(self):
        response = self.client.post(
            f"/api/cameras/{self.camera.id}/official-image/",
            {"captured_at": "2026-08-30T10:00:00+00:00", "image": SimpleUploadedFile("x.jpg", b"jpeg", content_type="image/jpeg")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        image_id = response.data["image_id"]
        response = self.client.post("/api/cv/ingest/", {
            "camera_id": self.camera.id,
            "image_id": image_id,
            "analysis": {"total_canopy_coverage": 42.5, "growth_change": 2.0, "crowding_percentage": 12.0, "green_percentage": 80.0, "yellow_percentage": 5.0, "quality_status": "PASS"},
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ImageAnalysis.objects.count(), 1)
        latest = self.client.get(f"/api/cv/cameras/{self.camera.id}/latest-analysis/")
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(latest.data["analysis"]["total_canopy_coverage"], "42.50")
        self.assertNotIn("measurements", latest.data)

    def test_duplicate_analysis_is_rejected(self):
        image = CameraImage.objects.create(camera=self.camera, captured_at=datetime.now(timezone.utc), path="camera_images/test.jpg")
        payload = {"camera_id": self.camera.id, "image_id": image.id, "analysis": {"measurement_valid": True}}
        self.assertEqual(self.client.post("/api/cv/ingest/", payload, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/cv/ingest/", payload, format="json").status_code, 409)
