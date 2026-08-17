import json
import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

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


# Tests written with AI assistance
class CVIngestTests(APITestCase):

    def setUp(self):
        """
        Runs before every test.

        Creates:
        - temporary media folder
        - authenticated user
        - test farm
        - test device
        - test farm level
        - test growing area
        - test slot
        - test camera
        """

        super().setUp()

        # ----------------------------------------------------
        # Use temporary MEDIA_ROOT for uploaded test images.
        #
        # This prevents tests from putting images inside the
        # project's real media/camera_images directory.
        # ----------------------------------------------------

        self.temp_media = tempfile.mkdtemp()

        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media
        )

        self.media_override.enable()

        # ----------------------------------------------------
        # Create authenticated user
        # ----------------------------------------------------

        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123!"
        )

        self.client.force_authenticate(
            user=self.user
        )

        # ----------------------------------------------------
        # Create minimum farm structure
        # ----------------------------------------------------

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

    def tearDown(self):
        """
        Runs after every test.

        Removes the temporary folder containing uploaded
        test images.
        """

        self.media_override.disable()

        shutil.rmtree(
            self.temp_media,
            ignore_errors=True
        )

        super().tearDown()

    # ========================================================
    # HELPER METHOD
    # ========================================================

    def create_test_image(self):
        """
        Creates a fake uploaded JPEG for multipart requests.

        It does not need to be a real plant image because these
        tests are testing Django ingest, not LeafyCV analysis.
        """

        return SimpleUploadedFile(
            "test.jpg",
            b"fake-image-data",
            content_type="image/jpeg"
        )

    # ========================================================
    # TEST 1
    # VALID INGEST
    # ========================================================

    def test_ingest_creates_cv_records(self):

        metadata = {
            "camera_id": self.camera.id,

            "captured_at":
                "2026-08-17T13:20:00+10:00",

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

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": self.create_test_image()
            },
            format="multipart"
        )

        # ----------------------------------------------------
        # Check API response
        # ----------------------------------------------------

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["measurement_count"],
            1
        )

        # ----------------------------------------------------
        # Check records were created
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Check CameraImage
        # ----------------------------------------------------

        camera_image = CameraImage.objects.get()

        self.assertEqual(
            camera_image.camera,
            self.camera
        )

        # Image should have been saved under camera_images/
        self.assertTrue(
            camera_image.path.name.startswith(
                "camera_images/"
            )
        )

        # Actual uploaded file should exist
        self.assertTrue(
            os.path.exists(
                camera_image.path.path
            )
        )

        # ----------------------------------------------------
        # Check ImageAnalysis values
        # ----------------------------------------------------

        analysis = ImageAnalysis.objects.get()

        self.assertEqual(
            analysis.image,
            camera_image
        )

        self.assertEqual(
            float(analysis.total_canopy_coverage),
            64.2
        )

        self.assertEqual(
            analysis.visible_plant_count,
            1
        )

        self.assertTrue(
            analysis.measurement_valid
        )

        self.assertEqual(
            analysis.processing_time_ms,
            128
        )

        # ----------------------------------------------------
        # Check PlantVisionMeasurement values
        # ----------------------------------------------------

        measurement = PlantVisionMeasurement.objects.get()

        self.assertEqual(
            measurement.image_analysis,
            analysis
        )

        self.assertEqual(
            measurement.slot,
            self.slot
        )

        self.assertEqual(
            float(measurement.canopy_coverage),
            42.6
        )

        self.assertEqual(
            measurement.width_px,
            218
        )

        self.assertEqual(
            measurement.height_px,
            174
        )

        self.assertEqual(
            float(measurement.width_cm),
            13.6
        )

        self.assertEqual(
            float(measurement.height_cm),
            10.9
        )

        self.assertEqual(
            float(measurement.green_percentage),
            86.2
        )

        self.assertEqual(
            float(measurement.yellow_percentage),
            5.4
        )

        self.assertEqual(
            float(measurement.crowding_percentage),
            15.0
        )

        self.assertEqual(
            float(measurement.growth_change),
            3.2
        )

        self.assertTrue(
            measurement.visible
        )

        self.assertTrue(
            measurement.measurement_valid
        )

    # ========================================================
    # TEST 2
    # INVALID SLOT
    # ========================================================

    def test_ingest_rejects_invalid_slot(self):

        metadata = {
            "camera_id": self.camera.id,

            "captured_at":
                "2026-08-17T13:20:00+10:00",

            "analysis": {
                "total_canopy_coverage": 20,
                "visible_plant_count": 1,
                "measurement_valid": True,
                "processing_time_ms": 100
            },

            "plants": [
                {
                    "slot_id": 99999,
                    "canopy_coverage": 10,
                    "visible": True,
                    "measurement_valid": True
                }
            ]
        }

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": self.create_test_image()
            },
            format="multipart"
        )

        # Request should be rejected
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        # Make sure it failed for the correct reason
        self.assertIn(
            "Unknown slot_id",
            response.data["error"]
        )

        # Nothing should have been written
        self.assertEqual(
            CameraImage.objects.count(),
            0
        )

        self.assertEqual(
            ImageAnalysis.objects.count(),
            0
        )

        self.assertEqual(
            PlantVisionMeasurement.objects.count(),
            0
        )

    # ========================================================
    # TEST 3
    # DUPLICATE SLOT
    # ========================================================

    def test_ingest_rejects_duplicate_slot(self):

        plant = {
            "slot_id": self.slot.id,
            "canopy_coverage": 10,
            "visible": True,
            "measurement_valid": True
        }

        metadata = {
            "camera_id": self.camera.id,

            "captured_at":
                "2026-08-17T13:20:00+10:00",

            "analysis": {
                "total_canopy_coverage": 20,
                "visible_plant_count": 1,
                "measurement_valid": True,
                "processing_time_ms": 100
            },

            "plants": [
                plant,
                plant
            ]
        }

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": self.create_test_image()
            },
            format="multipart"
        )

        # Duplicate SLOT should be rejected
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.data["error"],
            "Duplicate slot_id in measurements"
        )

        # ----------------------------------------------------
        # This is important:
        #
        # Verify the failed ingest did NOT leave partial
        # database records behind.
        # ----------------------------------------------------

        self.assertEqual(
            CameraImage.objects.count(),
            0
        )

        self.assertEqual(
            ImageAnalysis.objects.count(),
            0
        )

        self.assertEqual(
            PlantVisionMeasurement.objects.count(),
            0
        )

    # ========================================================
    # TEST 4
    # MAGENTA / NULL MEASUREMENTS
    # ========================================================

    def test_ingest_accepts_null_colour_and_size_measurements(self):

        # Simulate camera using MAGENTA grow lighting
        self.camera.lighting_mode = "MAGENTA"

        self.camera.save(
            update_fields=["lighting_mode"]
        )

        metadata = {
            "camera_id": self.camera.id,

            "captured_at":
                "2026-08-17T13:20:00+10:00",

            "analysis": {
                "total_canopy_coverage": 50.5,
                "visible_plant_count": 1,
                "measurement_valid": True,
                "processing_time_ms": 120
            },

            "plants": [
                {
                    "slot_id": self.slot.id,

                    "canopy_coverage": 40.5,

                    "width_px": 200,
                    "height_px": 160,

                    # No valid calibration available
                    "width_cm": None,
                    "height_cm": None,

                    # Colour readings are invalid under
                    # MAGENTA grow lighting
                    "green_percentage": None,
                    "yellow_percentage": None,

                    "crowding_percentage": 12.5,

                    "growth_change": 2.0,

                    "visible": True,
                    "measurement_valid": True
                }
            ]
        }

        response = self.client.post(
            "/api/cv/ingest/",
            {
                "metadata": json.dumps(metadata),
                "raw_image": self.create_test_image()
            },
            format="multipart"
        )

        # Request should still be accepted
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

        measurement = PlantVisionMeasurement.objects.get()

        # ----------------------------------------------------
        # Verify nullable measurements are actually NULL
        # ----------------------------------------------------

        self.assertIsNone(
            measurement.width_cm
        )

        self.assertIsNone(
            measurement.height_cm
        )

        self.assertIsNone(
            measurement.green_percentage
        )

        self.assertIsNone(
            measurement.yellow_percentage
        )

        # Other measurements should still be available
        self.assertEqual(
            float(measurement.canopy_coverage),
            40.5
        )

        self.assertEqual(
            measurement.width_px,
            200
        )

        self.assertEqual(
            measurement.height_px,
            160
        )