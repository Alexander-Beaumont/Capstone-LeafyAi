import unittest

from leafycv.config import config_from_backend


class BackendConfigTests(unittest.TestCase):
    def test_backend_camera_and_slot_positions_convert_to_internal_config(self):
        camera = {
            "camera_id": "cam-uuid",
            "name": "Level 1 Camera 1",
            "source_type": "RTSP",
            "ip_address": "192.168.1.106",
            "rtsp_port": 554,
            "rtsp_path": "/stream1",
            "lighting_mode": "MAGENTA",
            "roi_points": {"x": 0.1, "y": 0.2, "width": 0.8, "height": 0.7},
            "calibration_start_x": 0.2,
            "calibration_start_y": 0.8,
            "calibration_end_x": 0.5,
            "calibration_end_y": 0.8,
            "calibration_length_cm": 20.0,
            "enabled": True,
        }
        slots = [
            {"slot_id": "slot-1", "slot_label": "P01", "centre_x": 0.25, "centre_y": 0.45},
            {"slot_id": "slot-2", "slot_label": "P02", "centre_x": 0.55, "centre_y": 0.45},
        ]
        config = config_from_backend(camera, slots)
        self.assertEqual(config["camera"]["camera_id"], "cam-uuid")
        self.assertEqual(config["camera"]["rtsp"]["ip_address"], "192.168.1.106")
        self.assertEqual(config["lighting_mode"], "MAGENTA")
        self.assertEqual(config["calibration_stick"]["length_cm"], 20.0)
        self.assertEqual(config["slots"][0]["slot_id"], "slot-1")
        self.assertEqual(config["slots"][0]["label"], "P01")


if __name__ == "__main__":
    unittest.main()
