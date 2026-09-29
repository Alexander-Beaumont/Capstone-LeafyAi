from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from telemetry.models import Farm, FarmDevice, FarmLevel, GrowingArea


class GrowthAreaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(username="tester"))
        self.farm = Farm.objects.create(name="North rack", location="Lab")
        self.other = Farm.objects.create(name="South rack", location="")

    def test_create_and_list_growing_area_for_the_selected_farm(self):
        response = self.client.post(
            "/api/create-growing-area/",
            {"name": "Main", "farmLevel": 1, "slotCount": 12, "farm_id": self.farm.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        area = GrowingArea.objects.get()
        self.assertEqual(area.slot_count, 12)
        self.assertEqual(area.farm_level.device.farm_id, self.farm.id)
        self.assertEqual(area.farm_level.level_number, 1)

        listed = self.client.get("/api/growing-areas", {"farm_id": self.farm.id})
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data[0]["slotCount"], 12)

        other = self.client.get("/api/growing-areas", {"farm_id": self.other.id})
        self.assertEqual(other.status_code, 200)
        self.assertEqual(other.data, [])

    def test_growing_areas_require_a_farm(self):
        missing = self.client.get("/api/growing-areas")
        self.assertEqual(missing.status_code, 400)

    def test_update_keeps_the_area_on_the_selected_farm(self):
        device = FarmDevice.objects.create(farm=self.farm, name="Controller", device_type="controller")
        level = FarmLevel.objects.create(device=device, level_number=1)
        area = GrowingArea.objects.create(farm_level=level, name="Tray", slot_count=4)

        response = self.client.patch(
            "/api/update-growing-area/",
            {
                "growingAreaID": area.id,
                "farmLevel": 2,
                "slotCount": 8,
                "farm_id": self.farm.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        area.refresh_from_db()
        self.assertEqual(area.slot_count, 8)
        self.assertEqual(area.farm_level.level_number, 2)
        self.assertEqual(area.farm_level.device.farm_id, self.farm.id)

        wrong_farm = self.client.patch(
            "/api/update-growing-area/",
            {"growingAreaID": area.id, "name": "Nope", "farm_id": self.other.id},
            format="json",
        )
        self.assertEqual(wrong_farm.status_code, 404)
