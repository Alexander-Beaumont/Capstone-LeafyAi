from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun
from ai_agent.services import generate_recommendation
from core.operation_locks import operation_lock
from sensor_ingest.models import SensorIngestConfiguration
from sensor_ingest.services.collector import CollectionResult
from telemetry.farm_deletion import purge_farm
from telemetry.models import (
    ActuatorStateObservation,
    BatchPlacement,
    Camera,
    CameraImage,
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    PlantBatch,
    Sensor,
    SensorReading,
    SetpointObservation,
)


class Provider:
    provider_name = "test"
    model_name = "test-model"

    def __init__(self):
        self.calls = []

    def complete(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        return '{"image_observations":[],"recommendations":[{"device_id":null,"decision_type":"inspect","target_device":"none","device_state":"none","category":"alert","recommendation":"Inspect.","explanation":"Evidence.","confidence":0.8}]}'


class OperatorApiTests(APITestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.client.force_authenticate(User.objects.create_user("operator"))
        self.farm = Farm.objects.create(name="Operator farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Controller", slug="controller")
        self.level = FarmLevel.objects.create(device=self.device, level_number=1)

    def test_farm_list_is_paginated_and_ordered(self):
        earlier = Farm.objects.create(name="Second")
        response = self.client.get("/api/farms/?limit=20")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual([item["id"] for item in response.data["results"]], [self.farm.id, earlier.id])

    def test_farm_delete_purges_owned_history_and_camera_files(self):
        sensor = Sensor.objects.create(
            device=self.device, slug="ph", sensor_type="ph", unit="pH"
        )
        reading = SensorReading.objects.create(
            sensor=sensor, value=6.2, measured_at=timezone.now()
        )
        ActuatorStateObservation.objects.create(
            device=self.device,
            actuator_slug="pump",
            state="on",
            measured_at=timezone.now(),
        )
        SetpointObservation.objects.create(
            device=self.device,
            setpoint_slug="target-ph",
            value=6.0,
            unit="pH",
            measured_at=timezone.now(),
        )
        area = GrowingArea.objects.create(
            farm_level=self.level, name="Bed", slot_count=12
        )
        batch = PlantBatch.objects.create(
            plant_type="Lettuce",
            planting_date=timezone.localdate(),
            growth_stage="seedling",
            status="active",
        )
        BatchPlacement.objects.create(
            plant_batch=batch,
            growing_area=area,
            start_date=timezone.now(),
        )
        camera = Camera.objects.create(
            farm_level=self.level, name="Delete camera", source_type="RTSP"
        )
        image = CameraImage(
            camera=camera,
            captured_at=timezone.now(),
            vlm_ready=True,
            quality_status="PASS",
        )
        image.path.save("delete.jpg", ContentFile(b"delete-me"), save=False)
        image.save()
        deleted_image_path = Path(image.path.path)

        run = AIRecommendationRun.objects.create(
            farm=self.farm, status="completed"
        )
        AIConfiguration.objects.create(farm=self.farm)
        run.source_images.add(image)
        run.source_readings.add(reading)
        AIDecision.objects.create(
            run=run,
            device=self.device,
            decision_type="inspect",
            recommendation="Inspect",
            explanation="Test",
        )

        other_farm = Farm.objects.create(name="Other farm")
        other_device = FarmDevice.objects.create(
            farm=other_farm, name="Other controller"
        )
        other_sensor = Sensor.objects.create(
            device=other_device, slug="ph", sensor_type="ph", unit="pH"
        )
        other_reading = SensorReading.objects.create(
            sensor=other_sensor, value=7.0, measured_at=timezone.now()
        )

        self.assertTrue(deleted_image_path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f"/api/farms/{self.farm.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Farm.objects.filter(pk=self.farm.id).exists())
        self.assertFalse(FarmDevice.objects.filter(pk=self.device.id).exists())
        self.assertFalse(SensorReading.objects.filter(pk=reading.id).exists())
        self.assertFalse(CameraImage.objects.filter(pk=image.id).exists())
        self.assertFalse(AIRecommendationRun.objects.filter(pk=run.id).exists())
        self.assertFalse(AIConfiguration.objects.filter(farm_id=self.farm.id).exists())
        self.assertFalse(
            SensorIngestConfiguration.objects.filter(device_id=self.device.id).exists()
        )
        self.assertFalse(BatchPlacement.objects.filter(plant_batch=batch).exists())
        self.assertTrue(PlantBatch.objects.filter(pk=batch.id).exists())
        self.assertFalse(deleted_image_path.exists())
        self.assertTrue(Farm.objects.filter(pk=other_farm.id).exists())
        self.assertTrue(SensorReading.objects.filter(pk=other_reading.id).exists())

    def test_farm_delete_returns_404_when_farm_is_missing(self):
        response = self.client.delete("/api/farms/999999/")
        self.assertEqual(response.status_code, 404)

    def test_farm_delete_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(f"/api/farms/{self.farm.id}/")
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Farm.objects.filter(pk=self.farm.id).exists())

    def test_protected_history_still_blocks_direct_parent_deletion(self):
        sensor = Sensor.objects.create(
            device=self.device, slug="ec", sensor_type="ec", unit="uS/cm"
        )
        SensorReading.objects.create(
            sensor=sensor, value=1200, measured_at=timezone.now()
        )
        camera = Camera.objects.create(
            farm_level=self.level, name="Protected camera", source_type="RTSP"
        )
        CameraImage.objects.create(
            camera=camera,
            captured_at=timezone.now(),
            path="camera_images/protected.jpg",
        )

        with self.assertRaises(ProtectedError):
            sensor.delete()
        with self.assertRaises(ProtectedError):
            camera.delete()

    def test_farm_purge_rollback_keeps_database_and_image_file(self):
        camera = Camera.objects.create(
            farm_level=self.level, name="Rollback camera", source_type="RTSP"
        )
        image = CameraImage(camera=camera, captured_at=timezone.now())
        image.path.save("rollback.jpg", ContentFile(b"keep-me"), save=False)
        image.save()
        image_path = Path(image.path.path)

        with patch("telemetry.farm_deletion.Farm.delete", side_effect=RuntimeError("stop")):
            with self.assertRaisesRegex(RuntimeError, "stop"):
                purge_farm(self.farm.id)

        self.assertTrue(Farm.objects.filter(pk=self.farm.id).exists())
        self.assertTrue(CameraImage.objects.filter(pk=image.id).exists())
        self.assertTrue(image_path.exists())

    def test_farm_delete_logs_media_cleanup_failure_after_database_commit(self):
        camera = Camera.objects.create(
            farm_level=self.level, name="Storage error camera", source_type="RTSP"
        )
        image = CameraImage(camera=camera, captured_at=timezone.now())
        image.path.save("storage-error.jpg", ContentFile(b"orphan"), save=False)
        image.save()

        with patch.object(image.path.storage, "delete", side_effect=OSError("offline")):
            with self.assertLogs("telemetry.farm_deletion", level="WARNING"):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.delete(f"/api/farms/{self.farm.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Farm.objects.filter(pk=self.farm.id).exists())

    def test_ingest_patch_validates_lan_urls_and_updates_sensor_timing(self):
        sensor = Sensor.objects.create(device=self.device, slug="water-ph", sensor_type="ph", unit="pH")
        url = f"/api/farms/{self.farm.id}/sensor-ingest/{self.device.id}/"
        response = self.client.patch(url, {
            "water_quality_url": "http://192.168.1.10/readings",
            "ambient_sensor_url": "https://10.0.0.4:8443/readings",
            "poll_interval_seconds": 45,
            "sensor_stale_threshold_seconds": 180,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        sensor.refresh_from_db()
        self.assertEqual((sensor.expected_interval_seconds, sensor.stale_after_seconds), (45, 180))
        invalid = self.client.patch(url, {"water_quality_url": "http://user:pass@192.168.1.10/readings"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        public = self.client.patch(url, {"water_quality_url": "https://8.8.8.8/readings"}, format="json")
        self.assertEqual(public.status_code, 400)

    @patch("sensor_ingest.views.SensorCollector.collect")
    def test_manual_collection_returns_summary_and_updates_status(self, collect):
        configuration = SensorIngestConfiguration.objects.get(device=self.device)
        configuration.enabled = True
        configuration.water_quality_url = "http://192.168.1.10/readings"
        configuration.ambient_sensor_url = "http://192.168.1.11/readings"
        configuration.save()
        collected_at = timezone.now()
        collect.return_value = CollectionResult(5, ("humidity",), ("water-ph",), collected_at)
        response = self.client.post(
            f"/api/farms/{self.farm.id}/sensor-ingest/{self.device.id}/collect/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stored_count"], 5)
        self.assertEqual(response.data["missing_sensors"], ["humidity"])
        configuration.refresh_from_db()
        self.assertIsNotNone(configuration.last_success_at)

    def test_manual_collection_conflict_is_409(self):
        configuration = SensorIngestConfiguration.objects.get(device=self.device)
        configuration.enabled = True
        configuration.save()
        lock = operation_lock("sensor-collect", self.device.id)
        lock.acquire()
        try:
            response = self.client.post(
                f"/api/farms/{self.farm.id}/sensor-ingest/{self.device.id}/collect/"
            )
        finally:
            lock.release()
        self.assertEqual(response.status_code, 409)

    def test_sensor_history_aggregates_and_is_farm_isolated(self):
        sensor = Sensor.objects.create(device=self.device, slug="ec", sensor_type="ec", unit="uS/cm")
        now = timezone.now()
        SensorReading.objects.create(sensor=sensor, value=10, measured_at=now - timedelta(minutes=9))
        SensorReading.objects.create(sensor=sensor, value=20, measured_at=now - timedelta(minutes=8))
        other = Farm.objects.create(name="Other")
        other_device = FarmDevice.objects.create(farm=other, name="Other device")
        other_sensor = Sensor.objects.create(device=other_device, slug="ec", sensor_type="ec", unit="uS/cm")
        SensorReading.objects.create(sensor=other_sensor, value=999, measured_at=now - timedelta(minutes=8))
        response = self.client.get(
            f"/api/farms/{self.farm.id}/sensor-history/?preset=1h&bucket=15m&sensors=ec"
        )
        self.assertEqual(response.status_code, 200)
        points = response.data["series"][0]["points"]
        self.assertEqual(sum(point["sample_count"] for point in points), 2)
        self.assertLess(max(point["maximum"] for point in points), 999)

    def test_camera_crud_status_capture_and_gallery(self):
        create = self.client.post(f"/api/farms/{self.farm.id}/cameras/", {
            "farm_level_id": self.level.id,
            "name": "Top camera",
            "source_type": "RTSP",
            "ip_address": "192.168.1.20",
            "rtsp_port": 554,
            "rtsp_path": "/stream1",
            "capture_interval_minutes": 30,
        }, format="json")
        self.assertEqual(create.status_code, 201)
        camera = Camera.objects.get(id=create.data["id"])
        self.assertEqual(create.data["schedule_state"], "due")

        def fake_capture(camera_payload, force=False):
            CameraImage.objects.create(
                camera=camera, captured_at=timezone.now(), path="camera_images/operator-test.jpg",
                vlm_ready=True, quality_status="PASS",
            )
            return True

        with patch("telemetry.operator_views.build_collector") as factory:
            factory.return_value.process_camera.side_effect = fake_capture
            response = self.client.post(
                f"/api/farms/{self.farm.id}/cameras/{camera.id}/capture/"
            )
        self.assertEqual(response.status_code, 201)
        gallery = self.client.get(
            f"/api/farms/{self.farm.id}/camera-images/?quality=PASS&vlm_ready=true"
        )
        self.assertEqual(gallery.data["count"], 1)
        self.assertFalse(gallery.data["results"][0]["ai_used"])
        archived = self.client.patch(
            f"/api/farms/{self.farm.id}/cameras/{camera.id}/",
            {"is_archived": True}, format="json",
        )
        self.assertFalse(archived.data["enabled"])
        refused = self.client.post(
            f"/api/farms/{self.farm.id}/cameras/{camera.id}/capture/"
        )
        self.assertEqual(refused.status_code, 400)

    def test_dashboard_and_missing_farm_do_not_fallback(self):
        response = self.client.get(f"/api/farms/{self.farm.id}/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["farm"]["id"], self.farm.id)
        self.assertIn("counts", response.data["sensors"])
        self.assertEqual(self.client.get("/api/farms/999999/dashboard/").status_code, 404)

    def test_ai_history_is_paginated_filtered_and_farm_scoped(self):
        completed = AIRecommendationRun.objects.create(farm=self.farm, status="completed", trigger="manual")
        AIRecommendationRun.objects.create(
            farm=self.farm, status="skipped", trigger="scheduled", skip_reason="No new evidence."
        )
        response = self.client.get(
            f"/api/ai-agent/farms/{self.farm.id}/recommendations/history/?status=skipped"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], "skipped")
        detail = self.client.get(
            f"/api/ai-agent/farms/{self.farm.id}/recommendations/{completed.id}/"
        )
        self.assertEqual(detail.status_code, 200)
        other = Farm.objects.create(name="Other AI farm")
        self.assertEqual(
            self.client.get(
                f"/api/ai-agent/farms/{other.id}/recommendations/{completed.id}/"
            ).status_code,
            404,
        )


class RecommendationFreshnessTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="AI farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Rack")
        self.level = FarmLevel.objects.create(device=self.device, level_number=1)
        self.sensor = Sensor.objects.create(
            device=self.device, slug="ec", sensor_type="ec", unit="uS/cm", stale_after_seconds=120
        )
        self.reading = SensorReading.objects.create(sensor=self.sensor, value=1500, measured_at=timezone.now())
        AIConfiguration.objects.create(farm=self.farm, max_image_age_minutes=60)

    def test_scheduled_run_skips_unchanged_evidence(self):
        previous = AIRecommendationRun.objects.create(farm=self.farm, status="completed")
        previous.source_readings.add(self.reading)
        provider = Provider()
        result = generate_recommendation(self.farm, provider=provider, trigger="scheduled", scheduled_for=timezone.now())
        self.assertEqual(result["status"], "skipped")
        self.assertIn("No new eligible", result["skip_reason"])
        self.assertEqual(provider.calls, [])

    def test_manual_run_allows_reuse_and_records_provenance(self):
        previous = AIRecommendationRun.objects.create(farm=self.farm, status="completed")
        previous.source_readings.add(self.reading)
        provider = Provider()
        result = generate_recommendation(self.farm, provider=provider, trigger="manual")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_readings"][0]["id"], self.reading.id)
        self.assertTrue(result["source_readings"][0]["reused"])
        self.assertEqual(len(provider.calls), 1)

    def test_stale_and_suspect_readings_are_not_sources(self):
        self.reading.measured_at = timezone.now() - timedelta(minutes=10)
        self.reading.save(update_fields=["measured_at"])
        provider = Provider()
        result = generate_recommendation(self.farm, provider=provider)
        self.assertEqual(result["source_readings"], [])
        self.assertEqual(result["input_freshness_summary"]["sensors"]["stale"], 1)

    def test_old_images_are_excluded_by_configured_age(self):
        camera = Camera.objects.create(
            farm_level=self.level, name="Old camera", source_type="RTSP"
        )
        old_image = CameraImage.objects.create(
            camera=camera,
            captured_at=timezone.now() - timedelta(minutes=61),
            path="camera_images/old.jpg",
            vlm_ready=True,
            quality_status="PASS",
        )
        result = generate_recommendation(self.farm, provider=Provider())
        self.assertEqual(result["source_images"], [])
        evidence = next(item for item in result["visual_evidence"] if item["image_id"] == old_image.id)
        self.assertIn("older", evidence["reason"])

    def test_partial_new_snapshot_runs_with_reused_and_new_readings(self):
        sensor_two = Sensor.objects.create(
            device=self.device, slug="ph", sensor_type="ph", unit="pH", stale_after_seconds=120
        )
        second = SensorReading.objects.create(
            sensor=sensor_two, value=6.3, measured_at=timezone.now()
        )
        previous = AIRecommendationRun.objects.create(farm=self.farm, status="completed")
        previous.source_readings.add(self.reading)
        result = generate_recommendation(
            self.farm, provider=Provider(), trigger="scheduled", scheduled_for=timezone.now()
        )
        self.assertEqual(result["status"], "completed")
        summary = result["input_freshness_summary"]
        self.assertEqual(summary["reused_reading_ids"], [self.reading.id])
        self.assertEqual(summary["new_reading_ids"], [second.id])
