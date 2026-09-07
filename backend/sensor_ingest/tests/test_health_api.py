from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from sensor_ingest.models import IngestionSourceState


@override_settings(SENSOR_INGEST_FEED_STALE_SECONDS=120)
class SensorIngestHealthApiTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username="operator", password="password")
        self.client.force_authenticate(user=user)

    def test_health_distinguishes_connection_and_feed_freshness(self):
        now = timezone.now()
        IngestionSourceState.objects.create(
            key="thingspeak-primary",
            provider="thingspeak",
            external_source_id="channel",
            last_attempt_at=now,
            last_http_success_at=now,
            last_source_entry_id=100,
            last_source_measured_at=now,
        )
        response = self.client.get("/api/sensor-ingest/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        source = response.data["sources"][0]
        self.assertEqual(source["collector_status"], "active")
        self.assertEqual(source["connection_status"], "online")
        self.assertEqual(source["feed_status"], "fresh")
