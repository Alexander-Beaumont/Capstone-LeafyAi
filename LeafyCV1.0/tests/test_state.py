import tempfile
import unittest
from pathlib import Path

from leafycv.state import apply_growth_and_temporal_checks, load_state, save_state


CONFIG = {
    "camera": {"name": "Test Camera"},
    "roi": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
    "slots": [{"slot_id": "slot-uuid-1", "centre": [0.5, 0.5]}],
}
ANALYSIS = {"max_zone_change_pp": 20.0, "max_slot_change_pp": 20.0}


class StateTests(unittest.TestCase):
    def test_growth_persists_across_process_style_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = load_state(path, CONFIG)
            first = [{"slot_id": "slot-uuid-1", "canopy_coverage": 40.0, "measurement_valid": True}]
            valid, _ = apply_growth_and_temporal_checks(
                results=first, total_canopy=40.0, image_valid=True, state=state, analysis_cfg=ANALYSIS
            )
            self.assertTrue(valid)
            self.assertEqual(first[0]["growth_change"], 0.0)
            save_state(path, state)

            reloaded = load_state(path, CONFIG)
            second = [{"slot_id": "slot-uuid-1", "canopy_coverage": 42.5, "measurement_valid": True}]
            valid, _ = apply_growth_and_temporal_checks(
                results=second, total_canopy=42.5, image_valid=True, state=reloaded, analysis_cfg=ANALYSIS
            )
            self.assertTrue(valid)
            self.assertAlmostEqual(second[0]["growth_change"], 2.5)


if __name__ == "__main__":
    unittest.main()
