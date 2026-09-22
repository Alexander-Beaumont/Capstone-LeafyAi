from datetime import time
from unittest.mock import MagicMock, call, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from ai_agent.actuators import execute_decision
from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction
from ai_agent.providers import OpenAICompatibleProvider, ProviderError
from ai_agent.scheduler import run_due_schedules, schedule_slot
from ai_agent.services import RecommendationGenerationError, generate_recommendation
from telemetry.models import Camera, CameraImage, Farm, FarmDevice, FarmLevel, Sensor, SensorReading


def output(target="none", state="none", category="alert", confidence=0.8):
    return '{"image_observations":[],"recommendations":[{"device_id":null,"decision_type":"test","target_device":"%s","device_state":"%s","category":"%s","recommendation":"Inspect farm.","explanation":"Current evidence.","confidence":%s}]}' % (target, state, category, confidence)


class Provider:
    provider_name = "test"
    model_name = "test-model"
    def __init__(self, value=None): self.value = value or output(); self.calls = []
    def complete(self, system, user, **kwargs): self.calls.append(kwargs); return self.value


class FailingProvider(Provider):
    def complete(self, *args, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("vision unavailable")


class SequenceProvider(Provider):
    def __init__(self, values):
        super().__init__()
        self.values = list(values)

    def complete(self, system, user, **kwargs):
        self.calls.append(kwargs)
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class RecommendationTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Farm")
        self.device = FarmDevice.objects.create(farm=self.farm, name="Rack")
        self.level = FarmLevel.objects.create(device=self.device, level_number=1)
        self.camera1 = Camera.objects.create(farm_level=self.level, name="One", source_type="RTSP")
        self.camera2 = Camera.objects.create(farm_level=self.level, name="Two", source_type="RTSP")
        sensor = Sensor.objects.create(device=self.device, sensor_type="ec", unit="uS/cm")
        SensorReading.objects.create(sensor=sensor, value=1500, measured_at=timezone.now())

    def image(self, camera, ready, status):
        return CameraImage.objects.create(camera=camera, captured_at=timezone.now(), path="camera_images/test.jpg", vlm_ready=ready, quality_status=status, quality_message="quality")

    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_uses_only_passing_images(self, _image):
        good = self.image(self.camera1, True, "WARN")
        bad = self.image(self.camera2, False, "FAIL")
        vlm = Provider()
        result = generate_recommendation(self.farm, provider=Provider(), vlm_provider=vlm)
        run = AIRecommendationRun.objects.get(id=result["id"])
        self.assertEqual(result["input_mode"], "vlm")
        self.assertEqual(list(run.source_images.values_list("id", flat=True)), [good.id])
        self.assertNotIn(bad.id, list(run.source_images.values_list("id", flat=True)))
        self.assertEqual(len(vlm.calls[0]["images"]), 1)

    def test_no_reliable_image_uses_llm(self):
        self.image(self.camera1, False, "FAIL")
        result = generate_recommendation(self.farm, provider=Provider())
        self.assertEqual(result["input_mode"], "llm")
        self.assertTrue(result["fallback_used"])

    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_vlm_failure_falls_back(self, _image):
        self.image(self.camera1, True, "PASS")
        result = generate_recommendation(self.farm, provider=Provider(), vlm_provider=FailingProvider())
        self.assertEqual(result["input_mode"], "llm")
        self.assertIn("vision unavailable", result["fallback_reason"])

    @patch("ai_agent.services.time.sleep")
    def test_invalid_llm_output_persists_failed_run_after_retries(self, sleep):
        provider = Provider("not-json")
        with self.assertRaises(RecommendationGenerationError):
            generate_recommendation(self.farm, provider=provider)
        self.assertEqual(len(provider.calls), 4)
        self.assertEqual(sleep.call_args_list, [call(1), call(2), call(4)])
        self.assertEqual(AIRecommendationRun.objects.get().status, "failed")

    @patch("ai_agent.services.time.sleep")
    def test_llm_retries_provider_and_schema_failures_until_success(self, sleep):
        provider = SequenceProvider([
            ProviderError("missing choices"),
            "not-json",
            '{"recommendations":[]}',
            output(),
        ])

        result = generate_recommendation(self.farm, provider=provider)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(provider.calls), 4)
        self.assertEqual(sleep.call_args_list, [call(1), call(2), call(4)])
        self.assertEqual(AIDecision.objects.count(), 1)

    @patch("ai_agent.services.time.sleep")
    def test_llm_does_not_retry_non_retryable_provider_failure(self, sleep):
        provider = SequenceProvider([
            ProviderError("invalid API key", retryable=False),
        ])

        with self.assertRaises(RecommendationGenerationError):
            generate_recommendation(self.farm, provider=provider)

        self.assertEqual(len(provider.calls), 1)
        sleep.assert_not_called()

    @patch("ai_agent.services.time.sleep")
    @patch("ai_agent.services._image_data_url", return_value="data:image/jpeg;base64,dGVzdA==")
    def test_vlm_is_single_attempt_then_llm_retries(self, _image, sleep):
        self.image(self.camera1, True, "PASS")
        vlm = FailingProvider()
        llm = SequenceProvider([ProviderError("temporary"), output()])

        result = generate_recommendation(self.farm, provider=llm, vlm_provider=vlm)

        self.assertEqual(result["input_mode"], "llm")
        self.assertEqual(len(vlm.calls), 1)
        self.assertEqual(len(llm.calls), 2)
        sleep.assert_called_once_with(1)

    @patch("ai_agent.services.execute_decision")
    def test_safe_fan_recommendation_is_automatic(self, execute):
        for kind, value in (("ambient_temperature", 31), ("humidity", 50)):
            sensor = Sensor.objects.create(device=self.device, sensor_type=kind, unit="unit")
            SensorReading.objects.create(sensor=sensor, value=value, measured_at=timezone.now())
        generate_recommendation(self.farm, provider=Provider(output("fans", "on", "climate", 0.9)))
        self.assertEqual(AIDecision.objects.get().execution_type, "automated")
        execute.assert_called_once()

    @patch("ai_agent.services.execute_decision")
    def test_other_targets_remain_notifications(self, execute):
        generate_recommendation(self.farm, provider=Provider(output("irrigation_pump", "on", "water", 0.9)))
        self.assertEqual(AIDecision.objects.get().execution_type, "notification")
        execute.assert_not_called()


class ProviderTests(TestCase):
    def setUp(self):
        self.provider = OpenAICompatibleProvider(
            "https://example.invalid/v1",
            "test-key",
            "test-model",
            "openrouter",
        )

    @patch("ai_agent.providers.requests.post")
    def test_missing_choices_reports_upstream_message_as_retryable(self, post):
        response = MagicMock(status_code=200)
        response.json.return_value = {"error": {"message": "upstream unavailable"}}
        post.return_value = response

        with self.assertRaisesRegex(ProviderError, "upstream unavailable") as caught:
            self.provider.complete("system", "user")

        self.assertTrue(caught.exception.retryable)

    @patch("ai_agent.providers.requests.post")
    def test_authentication_failure_is_not_retryable(self, post):
        response = MagicMock(status_code=401)
        response.json.return_value = {"error": {"message": "invalid API key"}}
        post.return_value = response

        with self.assertRaisesRegex(ProviderError, "invalid API key") as caught:
            self.provider.complete("system", "user")

        self.assertFalse(caught.exception.retryable)

class SchedulerTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name="Scheduled")
        FarmDevice.objects.create(farm=self.farm, name="Rack")
        self.config = AIConfiguration.objects.create(farm=self.farm, schedule_enabled=True, timezone="Australia/Melbourne", active_start_time=time(8), active_end_time=time(20), interval_minutes=30)

    def test_duplicate_slot_runs_once(self):
        now = timezone.now().replace(hour=1, minute=5, second=0, microsecond=0)
        # Use a 24-hour-like overnight window so this UTC test instant is eligible.
        self.config.active_start_time, self.config.active_end_time = time(20), time(19)
        self.config.save()
        with patch("ai_agent.scheduler.generate_recommendation"):
            run_due_schedules(now); run_due_schedules(now)
        self.assertEqual(AIRecommendationRun.objects.count(), 1)


class ActuatorTests(TestCase):
    def setUp(self):
        farm = Farm.objects.create(name="Hardware")
        device = FarmDevice.objects.create(farm=farm, name="Rack")
        run = AIRecommendationRun.objects.create(farm=farm, status="completed")
        self.decision = AIDecision.objects.create(run=run, device=device, decision_type="fan", execution_type="automated", target_device="fans", device_state="on", category="climate", recommendation="Fan on", explanation="Hot", confidence_score="0.90")

    @patch("ai_agent.actuators.get_powerboard_bridge")
    def test_fan_uses_current_powerboard_device_and_audits_confirmation(self, bridge_factory):
        bridge = bridge_factory.return_value
        bridge.get_all_device_statuses.return_value = [{"device_id": 4, "state": "OFF"}]
        bridge.set_device_state.return_value = {"device_id": 4, "state": "ON"}
        execute_decision(self.decision)
        bridge.set_device_state.assert_called_once_with(4, "ON")
        action = FarmAction.objects.get()
        self.assertEqual(action.powerboard_device_ids, [4])
        self.assertEqual((action.previous_state, action.confirmed_state, action.result), ("off", "on", "success"))

    @patch("ai_agent.actuators.get_powerboard_bridge")
    def test_light_uses_grouped_current_powerboard_operation(self, bridge_factory):
        self.decision.target_device = "light"
        self.decision.category = "lighting"
        self.decision.save(update_fields=["target_device", "category"])
        bridge = bridge_factory.return_value
        bridge.get_all_device_statuses.return_value = [
            {"device_id": 5, "state": "OFF"},
            {"device_id": 6, "state": "OFF"},
        ]
        bridge.set_device_state.side_effect = [
            {"device_id": 5, "state": "ON"},
            {"device_id": 6, "state": "ON"},
        ]
        execute_decision(self.decision)
        self.assertEqual(
            bridge.set_device_state.call_args_list,
            [call(5, "ON"), call(6, "ON")],
        )
        action = FarmAction.objects.get()
        self.assertEqual(action.powerboard_device_ids, [5, 6])
        self.assertEqual(action.result, "success")

    @patch("ai_agent.actuators.get_powerboard_bridge")
    def test_light_records_partial_result_when_one_outlet_fails(self, bridge_factory):
        self.decision.target_device = "light"
        self.decision.category = "lighting"
        self.decision.save(update_fields=["target_device", "category"])
        bridge = bridge_factory.return_value
        bridge.get_all_device_statuses.return_value = [
            {"device_id": 5, "state": "OFF"},
            {"device_id": 6, "state": "ON"},
        ]
        bridge.set_device_state.side_effect = [
            {"device_id": 5, "state": "ON"},
            RuntimeError("outlet unavailable"),
        ]

        execute_decision(self.decision)

        action = FarmAction.objects.get()
        self.assertEqual(action.previous_state, "mixed")
        self.assertEqual(action.confirmed_state, "mixed")
        self.assertEqual(action.result, "partial")
        self.assertEqual(action.hardware_response["errors"][0]["device_id"], 6)


class RecommendationApiTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user("ai-user"))
        self.farm = Farm.objects.create(name="API Farm")
        FarmDevice.objects.create(farm=self.farm, name="Rack")

    def test_settings_and_generation_are_farm_scoped(self):
        settings_url = f"/api/ai-agent/farms/{self.farm.id}/settings/"
        self.assertEqual(self.client.get(settings_url).status_code, 200)
        with patch("ai_agent.services.get_provider", return_value=Provider()):
            response = self.client.post(f"/api/ai-agent/farms/{self.farm.id}/recommendations/generate/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["farm"], self.farm.id)

    def test_audit_endpoints_are_read_only(self):
        self.assertEqual(self.client.post("/api/ai-decisions/", {}).status_code, 405)
        self.assertEqual(self.client.post("/api/actions/", {}).status_code, 405)
