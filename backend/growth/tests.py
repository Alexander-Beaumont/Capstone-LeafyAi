from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from telemetry.models import GrowingArea


class GrowthAreaTests(TestCase):
    def test_create_and_list_growing_area_with_slot_count(self):
        client = APIClient()
        client.force_authenticate(get_user_model().objects.create_user(username="tester"))
        response = client.post(
            "/api/create-growing-area/",
            {"name": "Main", "farmLevel": 1, "slotCount": 12},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GrowingArea.objects.get().slot_count, 12)
        listed = client.get("/api/growing-areas")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data[0]["slotCount"], 12)
