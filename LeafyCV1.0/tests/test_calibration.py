import unittest

from leafycv.calibration import pixels_per_cm


class CalibrationTests(unittest.TestCase):
    def test_pixels_per_cm_from_reference_line(self):
        config = {
            "calibration_stick": {
                "start": [0.10, 0.50],
                "end": [0.30, 0.50],
                "length_cm": 20.0,
            }
        }
        # 0.20 * 1000 px = 200 px, therefore 10 px/cm.
        self.assertAlmostEqual(pixels_per_cm(config, 1000, 500), 10.0, places=4)

    def test_missing_calibration_returns_none(self):
        self.assertIsNone(pixels_per_cm({}, 1000, 500))


if __name__ == "__main__":
    unittest.main()
