from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from telemetry.models import Farm

from .models import PowerboardConfiguration
from .services.configuration import bootstrap_environment_configuration


class PowerboardConfigurationAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="powerboard-test",
            password="test-password",
        )
        self.client.force_authenticate(self.user)
        self.farm = Farm.objects.create(name="Test Farm", location="Lab")
        self.url = reverse("farm-powerboard-config", args=[self.farm.id])

    def test_get_creates_empty_farm_configuration(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["farm_id"], self.farm.id)
        self.assertIsNone(response.data["powerboard_1_ip"])
        self.assertIsNone(response.data["powerboard_2_ip"])
        self.assertTrue(PowerboardConfiguration.objects.filter(farm=self.farm).exists())

    def test_patch_saves_two_powerboard_ips(self):
        response = self.client.patch(
            self.url,
            {
                "powerboard_1_ip": "192.168.1.102",
                "powerboard_2_ip": "192.168.1.101",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["powerboard_1_ip"], "192.168.1.102")
        self.assertEqual(response.data["powerboard_2_ip"], "192.168.1.101")

    def test_patch_rejects_invalid_ip(self):
        response = self.client.patch(
            self.url,
            {"powerboard_1_ip": "not-an-ip"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


@override_settings(
    LEAFY_POWERBOARD_1_IP="192.168.1.102",
    LEAFY_POWERBOARD_2_IP="192.168.1.101",
)
class PowerboardBootstrapTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Bootstrap Farm", location="Lab")

    def test_environment_values_seed_first_configuration(self):
        configuration, created = bootstrap_environment_configuration(self.farm)

        self.assertTrue(created)
        self.assertEqual(str(configuration.powerboard_1_ip), "192.168.1.102")
        self.assertEqual(str(configuration.powerboard_2_ip), "192.168.1.101")

    def test_bootstrap_does_not_overwrite_farmer_edits(self):
        configuration = PowerboardConfiguration.objects.create(
            farm=self.farm,
            powerboard_1_ip="192.168.1.200",
            powerboard_2_ip="192.168.1.201",
        )

        returned, created = bootstrap_environment_configuration(self.farm)
        configuration.refresh_from_db()

        self.assertFalse(created)
        self.assertEqual(returned.pk, configuration.pk)
        self.assertEqual(str(configuration.powerboard_1_ip), "192.168.1.200")
        self.assertEqual(str(configuration.powerboard_2_ip), "192.168.1.201")
