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
)

from ai_agent.models import AIDecision
from ai_agent import providers
from ai_agent.parsing import parse_recommendation
from ai_agent.prompts import build_messages
from ai_agent.services import generate_recommendation, NoDeviceError


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
    Slot.objects.create(growing_area=area, slot_number=1)

    sensor = Sensor.objects.create(
        device=device, sensor_type="temperature", unit="°C"
    )
    SensorReading.objects.create(
        sensor=sensor,
        value=Decimal("24.5"),
        timestamp=timezone.now(),
    )

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
            '"recommendation": "Add nutrient A", '
            '"explanation": "EC looks low.", '
            '"confidence": 0.9}'
        )
        self.assertFalse(parsed.used_fallback)
        self.assertEqual(parsed.decision_type, "dosing_adjustment")
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
        self.assertEqual(
            decision.recommendation, "Check tank level and sensor readings."
        )
        self.assertEqual(decision.confidence_score, Decimal("0.80"))

    def test_generate_recommendation_without_persist(self):
        result = generate_recommendation(
            self.farm, provider=providers.MockProvider(), persist=False
        )
        self.assertIsNone(result["decision_id"])
        self.assertEqual(AIDecision.objects.count(), 0)

    def test_no_device_raises(self):
        empty_farm = Farm.objects.create(name="Empty", location="Nowhere")
        with self.assertRaises(NoDeviceError):
            generate_recommendation(
                empty_farm, provider=providers.MockProvider()
            )


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
        self.assertTrue(AIDecision.objects.filter(id=data["decision_id"]).exists())

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
