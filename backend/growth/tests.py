from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from telemetry.models import (
    BatchPlacement,
    Camera,
    CameraImage,
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    PlantBatch,
    Slot,
)

from cv.models import ImageAnalysis, PlantVisionMeasurement


class GrowthAuthenticationTests(APITestCase):
    def test_growth_endpoints_require_authentication(self):
        endpoints = [
            ("get", "/api/growing-areas", None),
            ("get", "/api/batches", None),
            ("patch", "/api/move-batch", {}),
            ("post", "/api/create-growing-area", {}),
            ("patch", "/api/update-growing-area", {}),
            ("delete", "/api/delete-growing-area", {}),
            ("patch", "/api/update-batch", {}),
            ("post", "/api/create-batch", {}),
        ]

        for method, path, payload in endpoints:
            request = getattr(self.client, method)
            response = request(path, payload, format="json")

            with self.subTest(path=path):
                self.assertEqual(response.status_code, 401)


class MoveBatchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="Test123!")
        self.client.force_authenticate(user=self.user)

        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Test Device")
        level = FarmLevel.objects.create(device=device, level_number=1)

        self.area_a = GrowingArea.objects.create(
            farm_level=level,
            name="Greenhouse A",
            slot_count=24,
        )
        self.area_b = GrowingArea.objects.create(
            farm_level=level,
            name="Greenhouse B",
            slot_count=24,
        )
        self.batch = PlantBatch.objects.create(
            plant_type="Basil",
            planting_date=timezone.localdate(),
            growth_stage="seedling",
            status="active",
        )
        BatchPlacement.objects.create(
            plant_batch=self.batch,
            growing_area=self.area_a,
            start_date=timezone.now(),
        )

    def test_batch_can_move_back_to_previous_growing_area(self):
        first_response = self.client.patch(
            "/api/move-batch",
            {
                "batchID": str(self.batch.id),
                "currentGaID": str(self.area_a.id),
                "destinationGaID": str(self.area_b.id),
            },
            format="json",
        )
        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.patch(
            "/api/move-batch",
            {
                "batchID": str(self.batch.id),
                "currentGaID": str(self.area_b.id),
                "destinationGaID": str(self.area_a.id),
            },
            format="json",
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(BatchPlacement.objects.filter(plant_batch=self.batch).count(), 3)
        self.assertTrue(
            BatchPlacement.objects.filter(
                plant_batch=self.batch,
                growing_area=self.area_a,
                end_date__isnull=True,
            ).exists()
        )


class DeleteGrowingAreaTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="Test123!")
        self.client.force_authenticate(user=self.user)

        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Test Device")
        level = FarmLevel.objects.create(device=device, level_number=1)

        self.growing_area = GrowingArea.objects.create(
            farm_level=level,
            name="Greenhouse A",
            slot_count=2,
        )
        self.slot_1 = Slot.objects.create(growing_area=self.growing_area, slot_number=1)
        Slot.objects.create(growing_area=self.growing_area, slot_number=2)

        self.batch = PlantBatch.objects.create(
            plant_type="Basil",
            planting_date=timezone.localdate(),
            growth_stage="seedling",
            status="active",
        )
        BatchPlacement.objects.create(
            plant_batch=self.batch,
            growing_area=self.growing_area,
            start_date=timezone.now(),
        )
        self.camera = Camera.objects.create(
            farm_level=level,
            name="Test Camera",
            source_type="WEBCAM",
            webcam_index=0,
        )
        self.camera_image = CameraImage.objects.create(
            camera=self.camera,
            path="camera_images/test.jpg",
        )
        self.image_analysis = ImageAnalysis.objects.create(image=self.camera_image)
        self.measurement = PlantVisionMeasurement.objects.create(
            image_analysis=self.image_analysis,
            slot=self.slot_1,
        )

    def test_delete_growing_area_cascades_related_slots_and_placements(self):
        response = self.client.delete(
            "/api/delete-growing-area",
            {"growingAreaID": str(self.growing_area.id)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertFalse(GrowingArea.objects.filter(id=self.growing_area.id).exists())
        self.assertFalse(Slot.objects.filter(growing_area_id=self.growing_area.id).exists())
        self.assertFalse(
            BatchPlacement.objects.filter(growing_area_id=self.growing_area.id).exists()
        )
        self.assertFalse(
            PlantVisionMeasurement.objects.filter(id=self.measurement.id).exists()
        )
        self.assertTrue(ImageAnalysis.objects.filter(id=self.image_analysis.id).exists())
        self.assertTrue(CameraImage.objects.filter(id=self.camera_image.id).exists())
        self.assertTrue(PlantBatch.objects.filter(id=self.batch.id).exists())

    def test_delete_growing_area_returns_404_for_missing_id(self):
        response = self.client.delete(
            "/api/delete-growing-area",
            {"growingAreaID": "999999"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
