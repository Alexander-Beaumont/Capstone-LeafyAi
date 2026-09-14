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
