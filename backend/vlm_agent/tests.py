from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
import os
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from cv.models import ImageAnalysis
from rest_framework import status
from rest_framework.test import APITestCase
from telemetry.models import Camera, CameraImage, Farm, FarmDevice, FarmLevel
from vlm_agent.models import VLMDecision, VLMSafetyCheck
from vlm_agent.services import build_sensor_context, generate_recommendation
from vlm_agent import config


class RecordingMockProvider:
    model_name = "recording-mock-vlm"
    output = (
        '{"decision_type":"alert","execution_type":"notification",'
        '"target_device":"none","device_state":"none","category":"alert",'
        '"recommendation":"Inspect farm.","explanation":"Mock response.",'
        '"confidence":0.8}'
    )

    def __init__(self):
        self.calls = []

    def complete(self, system, user_text, image_data_url=None, **kwargs):
        self.calls.append({"system": system, "user_text": user_text, "image": image_data_url})
        return self.output


class VLMConfigEnvLoaderTests(SimpleTestCase):
    def test_env_file_loads_unset_values_without_overriding_shell(self):
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "VLM_TEST_FROM_FILE='file value'\n"
                "VLM_TEST_EXISTING=file value\n"
                "export VLM_TEST_EXPORT=exported\n"
            )
            with patch.dict(os.environ, {"VLM_TEST_EXISTING": "shell value"}, clear=False):
                os.environ.pop("VLM_TEST_FROM_FILE", None)
                os.environ.pop("VLM_TEST_EXPORT", None)
                config._load_env_file(env_path)

                self.assertEqual(os.environ["VLM_TEST_FROM_FILE"], "file value")
                self.assertEqual(os.environ["VLM_TEST_EXISTING"], "shell value")
                self.assertEqual(os.environ["VLM_TEST_EXPORT"], "exported")


class VLMRecommendationTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Test Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Test Device")
        level = FarmLevel.objects.create(device=self.device, level_number=1)
        self.camera = Camera.objects.create(name="Test Camera", farm_level=level, source_type="RTSP", ip_address="192.168.1.50", rtsp_port=554, rtsp_path="/stream1")

    def create_analysis(self, *, vlm_ready, quality_status="PASS", quality_message=""):
        image = CameraImage.objects.create(
            camera=self.camera,
            captured_at="2026-09-06T00:00:00Z",
            path=SimpleUploadedFile("farm.jpg", b"test-jpeg", content_type="image/jpeg"),
        )
        return ImageAnalysis.objects.create(
            image=image,
            vlm_ready=vlm_ready,
            quality_status=quality_status,
            quality_message=quality_message,
        )

    def test_ready_image_is_sent_to_vlm_and_persisted(self):
        analysis = self.create_analysis(vlm_ready=True)
        provider = RecordingMockProvider()

        result = generate_recommendation(self.farm, provider=provider)

        self.assertTrue(result["used_visual_input"])
        self.assertTrue(provider.calls[0]["image"].startswith("data:image/jpeg;base64,"))
        decision = VLMDecision.objects.get(id=result["decision_id"])
        self.assertEqual(decision.source_analysis, analysis)
        self.assertTrue(decision.used_visual_input)
        self.assertTrue(VLMSafetyCheck.objects.filter(decision=decision).exists())

    def test_failed_quality_uses_sensor_only_and_requires_review(self):
        analysis = self.create_analysis(
            vlm_ready=False,
            quality_status="FAIL",
            quality_message="Image is too blurry.",
        )
        provider = RecordingMockProvider()

        result = generate_recommendation(self.farm, provider=provider)

        self.assertFalse(result["used_visual_input"])
        self.assertIsNone(provider.calls[0]["image"])
        decision = VLMDecision.objects.get(id=result["decision_id"])
        self.assertEqual(decision.source_analysis, analysis)
        self.assertEqual(decision.visual_status, "QUALITY_REJECTED")
        self.assertEqual(decision.vlmsafetycheck.result, "requires_review")

    def test_sensor_context_excludes_cv_measurements(self):
        self.create_analysis(vlm_ready=True)

        camera = build_sensor_context(self.farm)["devices"][0]["levels"][0]["cameras"][0]

        self.assertNotIn("total_canopy_coverage", camera)
        self.assertNotIn("crowding_percentage", camera)
        self.assertNotIn("yellow_percentage", camera)


class VLMRecommendationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="vlm-user", password="test-password")
        self.farm = Farm.objects.create(name="API Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="API Device")

    def test_authenticated_endpoint_persists_sensor_only_decision(self):
        self.client.force_authenticate(self.user)
        provider = RecordingMockProvider()

        with patch("vlm_agent.services.get_provider", return_value=provider):
            response = self.client.post(
                "/api/vlm-agent/recommend/",
                {"farm_id": self.farm.id, "device_id": self.device.id},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["used_visual_input"])
        self.assertEqual(response.data["visual_evidence"]["status"], "NO_ANALYSIS")
        self.assertTrue(VLMDecision.objects.filter(id=response.data["decision_id"]).exists())
