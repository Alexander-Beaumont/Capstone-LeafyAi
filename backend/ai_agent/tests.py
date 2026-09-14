import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import Resolver404, resolve
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ai_agent import config
from ai_agent.models import AIDecision, FarmAction, SafetyCheck
from ai_agent.services import build_sensor_context, generate_recommendation
from cv.models import ImageAnalysis
from farm_state.services import build_farm_state
from telemetry.models import Camera, CameraImage, Farm, FarmDevice, FarmLevel, GrowingArea, Sensor, SensorReading


OUTPUT = (
    '{"decision_type":"alert","execution_type":"notification",'
    '"target_device":"none","device_state":"none","category":"alert",'
    '"recommendation":"Inspect farm.","explanation":"Fresh sensor evidence.",'
    '"confidence":0.8}'
)


class RecordingLLM:
    model_name = "recording-llm"

    def __init__(self, output=OUTPUT):
        self.output = output
        self.calls = []

    def complete(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        return self.output


class RecordingVLM(RecordingLLM):
    model_name = "recording-vlm"

    def complete(self, system, user, image_data_url=None, **kwargs):
        self.calls.append((system, user, {"image_data_url": image_data_url}))
        return self.output


class FailingVLM:
    model_name = "failing-vlm"

    def complete(self, *args, **kwargs):
        raise RuntimeError("vision unavailable")


class AIConfigEnvLoaderTests(SimpleTestCase):
    def test_env_file_loads_unset_values_without_overriding_shell(self):
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("LEAFY_AI_TEST_FROM_FILE='file value'\nLEAFY_AI_TEST_EXISTING=file value\n")
            with patch.dict(os.environ, {"LEAFY_AI_TEST_EXISTING": "shell value"}, clear=False):
                os.environ.pop("LEAFY_AI_TEST_FROM_FILE", None)
                config._load_env_file(env_path)
                self.assertEqual(os.environ["LEAFY_AI_TEST_FROM_FILE"], "file value")
                self.assertEqual(os.environ["LEAFY_AI_TEST_EXISTING"], "shell value")


class UnifiedRecommendationTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Test Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Test Device")
        self.level = FarmLevel.objects.create(device=self.device, level_number=1)
        self.camera = Camera.objects.create(name="Camera", farm_level=self.level, source_type="WEBCAM")
        sensor = Sensor.objects.create(device=self.device, sensor_type="ec", unit="uS/cm")
        SensorReading.objects.create(sensor=sensor, value="1500", measured_at=timezone.now())

    def create_analysis(self, *, ready, message=""):
        image = CameraImage.objects.create(camera=self.camera, captured_at=timezone.now(), path="camera_images/test.jpg")
        return ImageAnalysis.objects.create(image=image, vlm_ready=ready, quality_status="PASS" if ready else "FAIL", quality_message=message)

    def test_no_analysis_routes_to_llm_and_persists_unified_rows(self):
        llm = RecordingLLM()
        result = generate_recommendation(self.farm, provider=llm)
        decision = AIDecision.objects.get(pk=result["decision_id"])
        self.assertEqual(result["input_mode"], "llm")
        self.assertEqual(result["model_name"], "recording-llm")
        self.assertEqual(result["notification_status"], "ready")
        self.assertEqual(decision.execution_type, "notification")
        self.assertTrue(SafetyCheck.objects.filter(decision=decision).exists())
        self.assertFalse(FarmAction.objects.exists())

    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_quality_approved_image_routes_to_vlm(self, image_data):
        analysis = self.create_analysis(ready=True)
        vlm = RecordingVLM()
        result = generate_recommendation(self.farm, provider=RecordingLLM(), vlm_provider=vlm)
        decision = AIDecision.objects.get(pk=result["decision_id"])
        self.assertEqual(result["input_mode"], "vlm")
        self.assertEqual(result["model_name"], "recording-vlm")
        self.assertTrue(result["used_visual_input"])
        self.assertEqual(decision.source_analysis, analysis)
        self.assertEqual(vlm.calls[0][2]["image_data_url"], "data:image/jpeg;base64,dGVzdA==")

    def test_quality_rejected_image_routes_to_llm(self):
        self.create_analysis(ready=False, message="Image is blurry.")
        result = generate_recommendation(self.farm, provider=RecordingLLM())
        self.assertEqual(result["input_mode"], "llm")
        self.assertEqual(result["visual_evidence"]["status"], "QUALITY_REJECTED")
        self.assertFalse(result["fallback_used"])

    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_vlm_error_falls_back_to_llm_with_visible_reason(self, image_data):
        self.create_analysis(ready=True)
        result = generate_recommendation(self.farm, provider=RecordingLLM(), vlm_provider=FailingVLM())
        self.assertEqual(result["input_mode"], "llm")
        self.assertEqual(result["model_name"], "recording-llm")
        self.assertTrue(result["fallback_used"])
        self.assertIn("vision unavailable", result["fallback_reason"])
        self.assertEqual(result["visual_evidence"]["status"], "VLM_PROVIDER_ERROR")

    @patch("ai_agent.services._image_data_url", side_effect=OSError("missing file"))
    def test_unreadable_quality_approved_image_falls_back_to_llm(self, image_data):
        self.create_analysis(ready=True)
        result = generate_recommendation(self.farm, provider=RecordingLLM())
        self.assertEqual(result["input_mode"], "llm")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["visual_evidence"]["status"], "IMAGE_UNREADABLE")

    def test_malformed_output_is_persisted_as_blocked(self):
        result = generate_recommendation(self.farm, provider=RecordingLLM("not-json"))
        self.assertEqual(result["notification_status"], "blocked")
        self.assertEqual(result["safety_check"]["result"], "failed")
        self.assertTrue(AIDecision.objects.get(pk=result["decision_id"]).output_used_fallback)

    def test_out_of_range_heat_supports_corrective_fan_notification(self):
        for sensor_type, value in (("ambient_temperature", "31"), ("humidity", "50")):
            sensor = Sensor.objects.create(device=self.device, sensor_type=sensor_type, unit="unit")
            SensorReading.objects.create(sensor=sensor, value=value, measured_at=timezone.now())
        output = (
            '{"decision_type":"fan_adjustment","execution_type":"automated",'
            '"target_device":"fans","device_state":"on","category":"climate",'
            '"recommendation":"Turn fans on.","explanation":"Temperature is high.",'
            '"confidence":0.9}'
        )
        result = generate_recommendation(self.farm, provider=RecordingLLM(output))
        self.assertEqual(result["safety_check"]["result"], "passed")
        self.assertEqual(result["recommendation"]["execution_type"], "notification")
        self.assertFalse(FarmAction.objects.exists())

    def test_low_confidence_and_missing_relevant_evidence_are_blocked(self):
        output = (
            '{"decision_type":"fan_adjustment","execution_type":"notification",'
            '"target_device":"fans","device_state":"on","category":"climate",'
            '"recommendation":"Turn fans on.","explanation":"Possible heat.",'
            '"confidence":0.4}'
        )
        result = generate_recommendation(self.farm, provider=RecordingLLM(output))
        self.assertEqual(result["safety_check"]["result"], "failed")
        self.assertIn("below 0.70", result["safety_check"]["explanation"])
        self.assertIn("ambient_temperature reading is missing", result["safety_check"]["explanation"])

    def test_sensor_context_excludes_cv_measurements(self):
        self.create_analysis(ready=True)
        camera = build_sensor_context(self.farm)["devices"][0]["levels"][0]["cameras"][0]
        self.assertNotIn("total_canopy_coverage", camera)
        self.assertNotIn("yellow_percentage", camera)

    def test_farm_state_still_contains_cameras_not_slots(self):
        GrowingArea.objects.create(farm_level=self.level, name="Main", slot_count=12)
        level = build_farm_state(self.farm)["devices"][0]["levels"][0]
        self.assertIn("cameras", level)
        self.assertNotIn("slots", level)


class RecommendationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ai-user", password="test-password")
        self.farm = Farm.objects.create(name="API Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="API Device")
        sensor = Sensor.objects.create(device=self.device, sensor_type="ec", unit="uS/cm")
        SensorReading.objects.create(sensor=sensor, value="1500", measured_at=timezone.now())
        self.client.force_authenticate(self.user)

    def test_recommend_endpoint_returns_notification_metadata(self):
        with patch("ai_agent.services.get_provider", return_value=RecordingLLM()):
            response = self.client.post("/api/ai-agent/recommend/", {"farm_id": self.farm.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["input_mode"], "llm")
        self.assertEqual(response.data["notification_status"], "ready")

    def test_audit_endpoints_are_read_only_and_removed_routes_are_gone(self):
        self.assertEqual(self.client.post("/api/ai-decisions/", {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.post("/api/actions/", {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        for path in ("/api/human-approvals/", "/api/vlm-decisions/", "/api/vlm-agent/recommend/"):
            with self.assertRaises(Resolver404):
                resolve(path)
