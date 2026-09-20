import json
from datetime import datetime, time
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ai_agent.actuators import execute_decision
from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction, KasaActuator
from ai_agent.scheduler import schedule_slot
from ai_agent.services import generate_recommendation
from farm_state.services import build_farm_state
from telemetry.models import Camera, CameraImage, Farm, FarmDevice, FarmLevel, Sensor, SensorReading


class RecordingProvider:
    provider_name = "test"
    model_name = "test-model"

    def __init__(self, output):
        self.output = output
        self.calls = []

    def complete(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        return self.output


def output_for(device_id, items=None, observations=None):
    items = items or [{
        "device_id": device_id,
        "decision_type": "alert",
        "target_device": "none",
        "device_state": "none",
        "category": "alert",
        "recommendation": "Inspect farm.",
        "explanation": "Fresh sensor evidence.",
        "confidence": 0.8,
    }]
    return json.dumps({"image_observations": observations or [], "recommendations": items})


class RecommendationTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Device")
        sensor = Sensor.objects.create(device=self.device, sensor_type="ec", unit="uS/cm")
        SensorReading.objects.create(sensor=sensor, value="1500", measured_at=timezone.now())

    def test_no_image_uses_llm_and_persists_run(self):
        result = generate_recommendation(self.farm, provider=RecordingProvider(output_for(self.device.id)))
        self.assertEqual(result["input_mode"], "llm")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(len(result["recommendations"]), 1)

    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_vlm_receives_latest_raw_image_per_camera(self, image_data):
        level = FarmLevel.objects.create(device=self.device, level_number=1)
        cameras = [Camera.objects.create(farm_level=level, name=f"Camera {i}", source_type="WEBCAM") for i in (1, 2)]
        for camera in cameras:
            CameraImage.objects.create(camera=camera, captured_at=timezone.now(), path="camera_images/test.jpg")
        observations = [{"camera_id": cameras[0].id, "observation": "Green leaves."}]
        vlm = RecordingProvider(output_for(self.device.id, observations=observations))
        result = generate_recommendation(self.farm, provider=RecordingProvider(output_for(self.device.id)), vlm_provider=vlm)
        self.assertEqual(result["input_mode"], "vlm")
        self.assertEqual(len(vlm.calls[0][2]["images"]), 2)
        self.assertEqual(result["image_observations"], observations)

    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_invalid_vlm_output_falls_back_to_llm(self, image_data):
        level = FarmLevel.objects.create(device=self.device, level_number=1)
        camera = Camera.objects.create(farm_level=level, name="Camera", source_type="WEBCAM")
        CameraImage.objects.create(camera=camera, captured_at=timezone.now(), path="camera_images/test.jpg")
        result = generate_recommendation(
            self.farm,
            provider=RecordingProvider(output_for(self.device.id)),
            vlm_provider=RecordingProvider("not-json"),
        )
        self.assertEqual(result["input_mode"], "llm")
        self.assertIn("VLM failed", result["fallback_reason"])

    @patch("ai_agent.services.execute_decision")
    def test_multiple_items_only_execute_safe_fan_or_light(self, execute):
        for sensor_type, value in (("ambient_temperature", "31"), ("humidity", "50")):
            sensor = Sensor.objects.create(device=self.device, sensor_type=sensor_type, unit="unit")
            SensorReading.objects.create(sensor=sensor, value=value, measured_at=timezone.now())
        items = [
            {"device_id": self.device.id, "decision_type": "fan", "target_device": "fans", "device_state": "on", "category": "climate", "recommendation": "Turn fans on.", "explanation": "Temperature is high.", "confidence": 0.9},
            {"device_id": self.device.id, "decision_type": "pump", "target_device": "irrigation_pump", "device_state": "on", "category": "water", "recommendation": "Inspect and run the pump.", "explanation": "Water needs attention.", "confidence": 0.9},
        ]
        result = generate_recommendation(self.farm, provider=RecordingProvider(output_for(self.device.id, items=items)))
        self.assertEqual(len(result["recommendations"]), 2)
        execute.assert_called_once()
        self.assertEqual(AIDecision.objects.get(target_device="irrigation_pump").execution_type, "notification")

    def test_farm_state_camera_has_raw_image_metadata_only(self):
        level = FarmLevel.objects.create(device=self.device, level_number=1)
        camera = Camera.objects.create(farm_level=level, name="Camera", source_type="WEBCAM")
        image = CameraImage.objects.create(camera=camera, captured_at=timezone.now(), path="camera_images/test.jpg")
        camera_state = build_farm_state(self.farm)["devices"][0]["levels"][0]["cameras"][0]
        self.assertEqual(camera_state["image_id"], image.id)
        self.assertNotIn("analysis_id", camera_state)
        self.assertNotIn("total_canopy_coverage", camera_state)


class SchedulerTests(TestCase):
    def test_slot_is_anchored_to_local_window_and_overnight_supported(self):
        farm = Farm.objects.create(name="Farm")
        config = AIConfiguration.objects.create(farm=farm, interval_minutes=30, active_start_time=time(8), active_end_time=time(20))
        now = datetime(2026, 9, 20, 10, 47, tzinfo=ZoneInfo("Australia/Melbourne"))
        self.assertEqual(schedule_slot(config, now).astimezone(ZoneInfo(config.timezone)).strftime("%H:%M"), "10:30")
        config.active_start_time, config.active_end_time = time(20), time(6)
        overnight = datetime(2026, 9, 21, 1, 5, tzinfo=ZoneInfo(config.timezone))
        self.assertIsNotNone(schedule_slot(config, overnight))


class KasaExecutionTests(TestCase):
    @patch("ai_agent.actuators._set_kasa_socket", new_callable=AsyncMock, return_value=("off", "on"))
    def test_each_enabled_mapping_gets_an_audited_action(self, set_socket):
        farm = Farm.objects.create(name="Farm")
        device = FarmDevice.objects.create(farm=farm, name="Device")
        run = AIRecommendationRun.objects.create(farm=farm, status="completed")
        decision = AIDecision.objects.create(
            run=run, device=device, decision_type="light", execution_type="automated",
            target_device="light", device_state="on", category="lighting",
            recommendation="Turn lights on.", explanation="Low light.", confidence_score="0.9",
        )
        KasaActuator.objects.create(farm=farm, name="Top light", target_device="light", host="192.168.1.101", child_index=1)
        KasaActuator.objects.create(farm=farm, name="Bottom light", target_device="light", host="192.168.1.101", child_index=2)
        actions = execute_decision(decision)
        self.assertEqual(len(actions), 2)
        self.assertEqual(FarmAction.objects.filter(result="success").count(), 2)
        self.assertEqual(set_socket.await_count, 2)


class RecommendationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="password")
        self.client.force_authenticate(self.user)
        self.farm = Farm.objects.create(name="Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Device")
        sensor = Sensor.objects.create(device=self.device, sensor_type="ec", unit="uS/cm")
        SensorReading.objects.create(sensor=sensor, value="1500", measured_at=timezone.now())

    def test_generate_latest_and_recent_three(self):
        provider = RecordingProvider(output_for(self.device.id))
        with patch("ai_agent.services.get_provider", return_value=provider):
            for _ in range(4):
                response = self.client.post(f"/api/ai-agent/farms/{self.farm.id}/recommendations/generate/", {}, format="json")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        latest = self.client.get(f"/api/ai-agent/farms/{self.farm.id}/recommendations/latest/")
        recent = self.client.get(f"/api/ai-agent/farms/{self.farm.id}/recommendations/recent/")
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(len(recent.data), 3)

    @patch.dict("os.environ", {"AI_SETTINGS_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii")})
    def test_settings_encrypt_and_mask_api_keys(self):
        response = self.client.patch(
            f"/api/ai-agent/farms/{self.farm.id}/settings/",
            {"llm_provider": "openrouter", "llm_model": "model", "llm_api_key": "secret-1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("secret-1234", str(response.data))
        self.assertEqual(response.data["llm_api_key_mask"], "••••1234")
        config = AIConfiguration.objects.get(farm=self.farm)
        self.assertNotIn("secret-1234", config.llm_api_key_encrypted)

    def test_removed_cv_routes_are_not_resolved(self):
        with self.assertRaises(Resolver404):
            resolve("/api/cv/cameras/1/latest-analysis/")
