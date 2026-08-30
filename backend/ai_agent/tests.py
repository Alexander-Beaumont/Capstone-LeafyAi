from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from telemetry.models import (
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    Slot,
    Sensor,
    SensorReading,
    NutrientTank,
    PlantBatch,
    BatchPlacement,
    Camera,
    CameraImage,
)

from cv.models import ImageAnalysis, PlantVisionMeasurement

from ai_agent.models import AIDecision, SafetyCheck
from ai_agent import providers
from ai_agent.parsing import parse_recommendation
from ai_agent.prompts import build_messages
from ai_agent.safety import run_safety_check
from ai_agent.services import generate_recommendation, NoDeviceError
from farm_state.services import build_farm_state


def seed_toy_farm():
    """Build a small farm with sensor, tank, and batch data."""
    farm = Farm.objects.create(name="Toy Farm", location="Lab")
    device = FarmDevice.objects.create(
        farm=farm, name="Toy Device", device_type="hydroponic"
    )
    level = FarmLevel.objects.create(device=device, level_number=1)
    area = GrowingArea.objects.create(
        farm_level=level, name="Seedling", slot_count=2
    )
    slot = Slot.objects.create(growing_area=area, slot_number=1)

    sensor_values = {
        "ec": ("uS/cm", "1500"),
        "ph": ("pH", "6.0"),
        "water_temperature": ("C", "20.0"),
        "ambient_temperature": ("C", "24.0"),
        "dew_point": ("C", "18.0"),
        "water_level": ("cm", "10.0"),
        "humidity": ("%", "50.0"),
    }
    for sensor_type, (unit, value) in sensor_values.items():
        sensor = Sensor.objects.create(
            device=device, sensor_type=sensor_type, unit=unit
        )
        SensorReading.objects.create(sensor=sensor, value=Decimal(value))

    NutrientTank.objects.create(
        device=device, capacity_l=Decimal("20.0"), current_level_l=Decimal("12.0")
    )

    batch = PlantBatch.objects.create(
        plant_type="Basil",
        planting_date=timezone.localdate(),
        growth_stage="seedling",
        status="active",
    )
    BatchPlacement.objects.create(
        plant_batch=batch, growing_area=area, start_date=timezone.now(), end_date=None
    )

    camera = Camera.objects.create(
        farm_level=level,
        name="Top Camera",
        source_type="WEBCAM",
        webcam_index=0,
    )
    image = CameraImage.objects.create(camera=camera, path="camera_images/test.jpg")
    analysis = ImageAnalysis.objects.create(
        image=image,
        total_canopy_coverage=Decimal("20.0"),
        visible_plant_count=1,
        measurement_valid=True,
    )
    PlantVisionMeasurement.objects.create(
        image_analysis=analysis,
        slot=slot,
        canopy_coverage=Decimal("20.0"),
        growth_stage="seedling",
        measurement_valid=True,
    )

    return farm, device


class ProviderTests(APITestCase):
    def test_mock_provider_returns_canned_output(self):
        provider = providers.MockProvider()
        self.assertEqual(provider.output, providers.MockProvider.DEFAULT_OUTPUT)
        text = provider.complete("system", "user")
        self.assertEqual(text, providers.MockProvider.DEFAULT_OUTPUT)

    def test_mock_provider_custom_output(self):
        provider = providers.MockProvider(output='{"recommendation": "hi"}')
        self.assertEqual(provider.complete("s", "u"), '{"recommendation": "hi"}')

    def test_openai_compatible_provider_builds_request(self):
        provider = providers.OpenAICompatibleProvider(
            base_url="https://example.test/v1", api_key="k123", model="m1"
        )
        fake_response = mock.Mock()
        fake_response.json.return_value = {
            "choices": [{"message": {"content": "the answer"}}]
        }
        with mock.patch("ai_agent.providers.requests.post", return_value=fake_response) as post:
            text = provider.complete("sys", "usr")

        self.assertEqual(text, "the answer")
        post.assert_called_once()
        call = post.call_args
        self.assertEqual(call.args[0], "https://example.test/v1/chat/completions")
        self.assertEqual(call.kwargs["headers"]["Authorization"], "Bearer k123")
        self.assertEqual(call.kwargs["json"]["model"], "m1")
        self.assertEqual(
            call.kwargs["json"]["messages"],
            [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "usr"},
            ],
        )

    @mock.patch("ai_agent.providers.config.AI_PROVIDER", "openrouter")
    @mock.patch("ai_agent.providers.config.OPENROUTER_MODEL", "model-x")
    @mock.patch("ai_agent.providers.config.OPENROUTER_API_KEY", "sk-1")
    def test_factory_selects_openrouter(self):
        self.assertIsInstance(providers.get_provider(), providers.OpenRouterProvider)

    @mock.patch("ai_agent.providers.config.AI_PROVIDER", "ollama")
    @mock.patch("ai_agent.providers.config.OLLAMA_MODEL", "llama3.2")
    def test_factory_selects_ollama(self):
        self.assertIsInstance(providers.get_provider(), providers.OllamaProvider)

    @mock.patch("ai_agent.providers.config.AI_PROVIDER", "mock")
    def test_factory_selects_mock(self):
        self.assertIsInstance(providers.get_provider(), providers.MockProvider)

    @mock.patch("ai_agent.providers.config.AI_PROVIDER", "bogus")
    def test_factory_raises_on_unknown_provider(self):
        with self.assertRaises(ValueError):
            providers.get_provider()


class ParsingTests(APITestCase):
    def test_valid_json(self):
        parsed = parse_recommendation(
            '{"decision_type": "dosing_adjustment", '
            '"execution_type": "notification", '
            '"target_device": "none", '
            '"device_state": "none", '
            '"category": "dosing", '
            '"recommendation": "Add nutrient A", '
            '"explanation": "EC looks low.", '
            '"confidence": 0.9}'
        )
        self.assertFalse(parsed.used_fallback)
        self.assertEqual(parsed.decision_type, "dosing_adjustment")
        self.assertEqual(parsed.execution_type, "notification")
        self.assertEqual(parsed.target_device, "none")
        self.assertEqual(parsed.device_state, "none")
        self.assertEqual(parsed.category, "dosing")
        self.assertEqual(parsed.recommendation, "Add nutrient A")
        self.assertEqual(parsed.confidence, 0.9)

    def test_fenced_json(self):
        parsed = parse_recommendation(
            '```json\n{"recommendation": "Ok", "confidence": 0.5}\n```'
        )
        self.assertFalse(parsed.used_fallback)
        self.assertEqual(parsed.recommendation, "Ok")

    def test_garbage_falls_back(self):
        parsed = parse_recommendation("I think you should water the plants.")
        self.assertTrue(parsed.used_fallback)
        self.assertEqual(parsed.recommendation, "I think you should water the plants.")
        self.assertIsNone(parsed.confidence)

    def test_confidence_clamped(self):
        parsed = parse_recommendation('{"recommendation": "x", "confidence": 5}')
        self.assertEqual(parsed.confidence, 1.0)
        parsed = parse_recommendation('{"recommendation": "x", "confidence": -2}')
        self.assertEqual(parsed.confidence, 0.0)


class PromptTests(APITestCase):
    def test_build_messages_includes_farm_state(self):
        system, user = build_messages({"farm_id": 42})
        self.assertIn("vertical-farming", system)
        self.assertIn("JSON", system)
        self.assertIn("42", user)


class ServiceTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.farm, self.device = seed_toy_farm()

    def test_generate_recommendation_persists_decision(self):
        result = generate_recommendation(
            self.farm, provider=providers.MockProvider()
        )

        self.assertEqual(result["farm_id"], self.farm.id)
        self.assertEqual(result["device_id"], self.device.id)
        self.assertFalse(result["used_fallback"])
        self.assertIsNotNone(result["decision_id"])

        decision = AIDecision.objects.get(id=result["decision_id"])
        self.assertEqual(decision.decision_type, "alert")
        self.assertEqual(decision.execution_type, "notification")
        self.assertEqual(decision.target_device, "none")
        self.assertEqual(decision.device_state, "none")
        self.assertEqual(decision.category, "alert")
        self.assertEqual(
            decision.recommendation, "Check tank level and sensor readings."
        )
        self.assertEqual(decision.confidence_score, Decimal("0.80"))
        self.assertEqual(result["safety_check"]["result"], "passed")
        self.assertTrue(
            SafetyCheck.objects.filter(decision=decision, result="passed").exists()
        )

    def test_generate_recommendation_without_persist(self):
        result = generate_recommendation(
            self.farm, provider=providers.MockProvider(), persist=False
        )
        self.assertIsNone(result["decision_id"])
        self.assertIsNone(result["safety_check"])
        self.assertEqual(AIDecision.objects.count(), 0)
        self.assertEqual(SafetyCheck.objects.count(), 0)

    def test_no_device_raises(self):
        empty_farm = Farm.objects.create(name="Empty", location="Nowhere")
        with self.assertRaises(NoDeviceError):
            generate_recommendation(
                empty_farm, provider=providers.MockProvider()
            )


class SafetyTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.farm, self.device = seed_toy_farm()

    def _decision(self, **overrides):
        defaults = {
            "device": self.device,
            "decision_type": "fan_adjustment",
            "execution_type": "automated",
            "target_device": "fans",
            "device_state": "on",
            "category": "climate",
            "recommendation": "Turn fans on.",
            "explanation": "Ambient conditions are in range.",
            "confidence_score": Decimal("0.90"),
        }
        defaults.update(overrides)
        return AIDecision.objects.create(**defaults)

    def test_safety_check_passes_in_range_low_risk_action(self):
        decision = self._decision()
        farm_state = build_farm_state(self.farm)

        result = run_safety_check(decision, farm_state)

        self.assertEqual(result["result"], "passed")
        self.assertEqual(SafetyCheck.objects.get(decision=decision).result, "passed")

    def test_safety_check_fails_out_of_range_sensor(self):
        sensor = Sensor.objects.get(device=self.device, sensor_type="ph")
        SensorReading.objects.create(sensor=sensor, value=Decimal("7.2"))
        decision = self._decision()
        farm_state = build_farm_state(self.farm)

        result = run_safety_check(decision, farm_state)

        self.assertEqual(result["result"], "failed")
        self.assertIn("ph value 7.2", result["explanation"])

    def test_safety_check_fails_invalid_automated_device(self):
        decision = self._decision(
            target_device="pump",
            recommendation="Run irrigation pump for 20 minutes.",
        )
        farm_state = build_farm_state(self.farm)

        result = run_safety_check(decision, farm_state)

        self.assertEqual(result["result"], "failed")
        self.assertIn("not configured for automated execution", result["explanation"])

    def test_safety_check_requires_review_for_stale_data(self):
        sensor = Sensor.objects.get(device=self.device, sensor_type="ec")
        old_time = timezone.now() - timezone.timedelta(hours=2)
        SensorReading.objects.filter(sensor=sensor).update(timestamp=old_time)
        decision = self._decision()
        farm_state = build_farm_state(self.farm)

        result = run_safety_check(decision, farm_state)

        self.assertEqual(result["result"], "requires_review")
        self.assertIn("ec reading is stale", result["explanation"])

    def test_safety_check_requires_review_for_manual_category(self):
        decision = self._decision(
            decision_type="dosing_adjustment",
            execution_type="notification",
            target_device="none",
            device_state="none",
            category="dosing",
            recommendation="Add Nutrient A and B manually.",
        )
        farm_state = build_farm_state(self.farm)

        result = run_safety_check(decision, farm_state)

        self.assertEqual(result["result"], "requires_review")
        self.assertIn("dosing actions require human review", result["explanation"])


class EndpointTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser", password="TestPassword123!"
        )
        self.client.force_authenticate(user=self.user)
        self.farm, _ = seed_toy_farm()

    def _post(self, payload):
        # Force the mock provider so tests never touch the network,
        # regardless of the host environment's AI_PROVIDER setting.
        with mock.patch(
            "ai_agent.services.get_provider",
            return_value=providers.MockProvider(),
        ):
            return self.client.post(
                "/api/ai-agent/recommend/",
                data=payload,
                format="json",
            )

    def test_recommend_creates_decision(self):
        response = self._post({"farm_id": self.farm.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["farm_id"], self.farm.id)
        self.assertIsNotNone(data["decision_id"])
        self.assertEqual(data["safety_check"]["result"], "passed")
        self.assertTrue(AIDecision.objects.filter(id=data["decision_id"]).exists())
        self.assertTrue(SafetyCheck.objects.filter(id=data["safety_check"]["id"]).exists())

    def test_recommend_requires_farm_id(self):
        response = self._post({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recommend_missing_farm(self):
        response = self._post({"farm_id": 999999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recommend_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/ai-agent/recommend/",
            data={"farm_id": self.farm.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
