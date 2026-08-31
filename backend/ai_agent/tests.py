<<<<<<< HEAD
from django.test import TestCase
from django.utils import timezone
from ai_agent.models import AIDecision
from telemetry.models import PlantBatch

class AIDecisionModelTests(TestCase):
    
    def setUp(self):
        """
        setUp runs automatically before every test. 
        We use it to create the prerequisite database objects.
        """
        # Create a mock PlantBatch with the required planting_date
        self.test_batch = PlantBatch.objects.create(
            planting_date=timezone.now().date()
        )

    def test_aidecision_links_to_plantbatch(self):
        """Test that a new AIDecision correctly links to a PlantBatch."""
        
        # 1. Create a new AIDecision and assign our mock batch as the foreign key
        decision = AIDecision.objects.create(
            plant_batch=self.test_batch,
            decision_type="Nutrient Adjustment",
            recommendation="Increase EC to 1500 uS/cm",
            explanation="EC is dropping below the target threshold for the vegetative stage.",
            confidence_score=0.92
        )

        # 2. Fetch the newly created decision from the database
        saved_decision = AIDecision.objects.get(id=decision.id)

        # 3. Assert that the linked PlantBatch is exactly the one we created
        self.assertEqual(saved_decision.plant_batch, self.test_batch)
        self.assertEqual(saved_decision.plant_batch.id, self.test_batch.id)
=======
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from ai_agent import config
from farm_state.services import build_farm_state
from telemetry.models import Farm, FarmDevice, FarmLevel, GrowingArea


class AIConfigEnvLoaderTests(SimpleTestCase):
    def test_env_file_loads_unset_values_without_overriding_shell(self):
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "LEAFY_AI_TEST_FROM_FILE='file value'",
                        "LEAFY_AI_TEST_EXISTING=file value",
                        "export LEAFY_AI_TEST_EXPORT=exported",
                    ]
                )
            )

            with patch.dict(os.environ, {"LEAFY_AI_TEST_EXISTING": "shell value"}, clear=False):
                os.environ.pop("LEAFY_AI_TEST_FROM_FILE", None)
                os.environ.pop("LEAFY_AI_TEST_EXPORT", None)
                config._load_env_file(env_path)

                self.assertEqual(os.environ["LEAFY_AI_TEST_FROM_FILE"], "file value")
                self.assertEqual(os.environ["LEAFY_AI_TEST_EXISTING"], "shell value")
                self.assertEqual(os.environ["LEAFY_AI_TEST_EXPORT"], "exported")


class FarmStateVisionTests(TestCase):
    def test_farm_state_has_camera_analyses_not_slots(self):
        farm = Farm.objects.create(name="Test Farm")
        device = FarmDevice.objects.create(farm=farm, name="Device")
        farm_level = FarmLevel.objects.create(device=device, level_number=1)
        GrowingArea.objects.create(farm_level=farm_level, name="Main", slot_count=12)
        level = build_farm_state(farm)["devices"][0]["levels"][0]
        self.assertIn("cameras", level)
        self.assertNotIn("slots", level)
        self.assertEqual(level["growing_areas"][0]["slot_count"], 12)
>>>>>>> f504721e64d9aad837c24599c8aed59986118f4a
