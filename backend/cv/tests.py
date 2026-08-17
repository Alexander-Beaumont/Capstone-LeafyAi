import json
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import (
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    Slot,
    Camera,
    CameraImage,
)

from cv.models import (
    ImageAnalysis,
    PlantVisionMeasurement,
)
#test below was written with ai

class CVIngestTests(APITestCase):

    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123!"
        )

        # Authenticate test client
        self.client.force_authenticate(user=self.user)

        # Create minimum farm structure
        self.farm = Farm.objects.create(
            name="Test Farm",
            location="La Trobe"
        )

        self.device = FarmDevice.objects.create(
            farm=self.farm,
            name="Test Device",
            device_type="hydroponic"
        )

        self.level = FarmLevel.objects.create(
            device=self.device,
            level_number=1
        )

        self.area = GrowingArea.objects.create(
            farm_level=self.level,
            name="Test Growing Area",
            slot_count=4
        )

        self.slot = Slot.objects.create(
            growing_area=self.area,
            slot_number=1
        )

        self.camera = Camera.objects.create(
            farm_level=self.level,
            name="Test Camera",
            position="Top",
            source_type="WEBCAM",
            webcam_index=0,
            lighting_mode="NORMAL",
            enabled=True
        )
    def test_ingest_creates_cv_records(self):

        metadata = {
            "camera_id": self.camera.id,
            "captured_at": "2026-08-17T13:20:00+10:00",
            "analysis": {
                "total_canopy_coverage": 64.2,
                "visible_plant_count": 1,
                "measurement_valid": True,
                "processing_time_ms": 128
            },
            "plants": [
                {
                    "slot_id": self.slot.id,
                    "canopy_coverage": 42.6,
                    "width_px": 218,
                    "height_px": 174,
                    "width_cm": 13.6,
                    "height_cm": 10.9,
                    "green_percentage": 86.2,
                    "yellow_percentage": 5.4,
                    "crowding_percentage": 15.0,
                    "growth_change": 3.2,
                    "visible": True,
                    "measurement_valid": True
                }
            ]
        }

        image = SimpleUploadedFile(
            "test.jpg",
            b"fake-image-data",
            content_type="image/jpeg"
        )

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": image
            },
            format="multipart"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            CameraImage.objects.count(),
            1
        )

        self.assertEqual(
            ImageAnalysis.objects.count(),
            1
        )

        self.assertEqual(
            PlantVisionMeasurement.objects.count(),
            1
        )
        analysis = ImageAnalysis.objects.first()

        self.assertEqual(
            float(analysis.total_canopy_coverage),
            64.2
        )

        self.assertEqual(
            analysis.visible_plant_count,
            1
        )

        measurement = PlantVisionMeasurement.objects.first()

        self.assertEqual(
            measurement.slot,
            self.slot
        )

        self.assertEqual(
            float(measurement.canopy_coverage),
            42.6
        )

        self.assertEqual(
            float(measurement.width_cm),
            13.6
        )
    def test_ingest_rejects_invalid_slot(self):

        metadata = {
            "camera_id": self.camera.id,
            "analysis": {
                "total_canopy_coverage": 20,
                "visible_plant_count": 1
            },
            "plants": [
                {
                    "slot_id": 99999,
                    "canopy_coverage": 10
                }
            ]
        }

        image = SimpleUploadedFile(
            "test.jpg",
            b"fake-image-data",
            content_type="image/jpeg"
        )

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": image
            },
            format="multipart"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            CameraImage.objects.count(),
            0
        )

        self.assertEqual(
            ImageAnalysis.objects.count(),
            0
        )
    def test_ingest_rejects_duplicate_slot(self):

        plant = {
            "slot_id": self.slot.id,
            "canopy_coverage": 10
        }

        metadata = {
            "camera_id": self.camera.id,
            "analysis": {
                "total_canopy_coverage": 20,
                "visible_plant_count": 1
            },
            "plants": [
                plant,
                plant
            ]
        }

        image = SimpleUploadedFile(
            "test.jpg",
            b"fake-image-data",
            content_type="image/jpeg"
        )

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": image
            },
            format="multipart"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )