from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import Farm, FarmDevice, Sensor, SensorReading


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
