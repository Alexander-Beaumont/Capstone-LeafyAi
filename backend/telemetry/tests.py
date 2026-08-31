from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework import status
from telemetry.models import Sensor, SensorReading

class TelemetryModelTests(TestCase):
    
    def setUp(self):
        """
        Create the prerequisite database objects.
        A Sensor requires a 'sensor_type' and a 'unit'.
        """
        self.test_sensor = Sensor.objects.create(
            sensor_type="pH Sensor",
            unit="pH"
        )

    def test_sensor_reading_creation(self):
        """Test that a new SensorReading correctly links to a Sensor."""
        
        #Create a mock reading using the sensor built in setUp
        reading = SensorReading.objects.create(
            sensor=self.test_sensor,
            value=6.75
        )

        #Fetch it from the test database
        saved_reading = SensorReading.objects.get(id=reading.id)

        #Assert that the link is correct and the value matches
        self.assertEqual(saved_reading.sensor, self.test_sensor)
        self.assertEqual(saved_reading.value, 6.75)

class SensorAPIIntegrationTests(APITestCase):
    
    def setUp(self):
        """Set up the mock database just like a unit test."""
        self.sensor = Sensor.objects.create(
            sensor_type="EC Sensor",
            unit="uS/cm"
        )
        
        # NOTE: You may need to change this URL depending on what is written
        # inside your backend's main urls.py file!
        self.api_url = '/api/sensorreadings/' 

    def test_sensor_can_post_new_reading(self):
        """Simulate your ESP32 sending a POST request to the API."""
        
        # 1. The exact JSON payload your sensor script will send
        payload = {
            "sensor": self.sensor.id,
            "value": 1450.5
        }

        # 2. Fire an actual HTTP POST request to your backend
        response = self.client.post(self.api_url, data=payload, format='json')

        # 3. Assert the API responded with a "201 Created" success code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 4. Query the database to ensure the data actually saved
        self.assertEqual(SensorReading.objects.count(), 1)
        self.assertEqual(SensorReading.objects.first().value, 1450.5)
