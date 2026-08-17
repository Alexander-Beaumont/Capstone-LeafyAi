from django.test import TestCase
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
        