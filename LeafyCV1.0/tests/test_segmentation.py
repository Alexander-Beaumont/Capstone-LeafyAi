import unittest
import cv2
from pathlib import Path

from leafycv.config import load_config, normalized_roi_to_pixels
from leafycv.segmentation import segment_vegetation

ROOT = Path(__file__).resolve().parents[1]


class SegmentationTests(unittest.TestCase):
    def test_normal_demo_has_detected_vegetation(self):
        config = load_config(ROOT / "configs" / "demo_normal.json")
        frame = cv2.imread(config["camera"]["file_path"])
        x, y, w, h = normalized_roi_to_pixels(config["roi"], frame.shape[1], frame.shape[0])
        zone = frame[y:y+h, x:x+w]
        masks = segment_vegetation(zone, "NORMAL", config["segmentation"], config["analysis"])
        self.assertGreater(cv2.countNonZero(masks["combined"]), 1000)

    def test_magenta_demo_returns_mask_with_correct_shape(self):
        config = load_config(ROOT / "configs" / "demo_magenta.json")
        frame = cv2.imread(config["camera"]["file_path"])
        x, y, w, h = normalized_roi_to_pixels(config["roi"], frame.shape[1], frame.shape[0])
        zone = frame[y:y+h, x:x+w]
        masks = segment_vegetation(zone, "MAGENTA", config["segmentation"], config["analysis"])
        self.assertEqual(masks["combined"].shape, zone.shape[:2])


if __name__ == "__main__":
    unittest.main()
