import unittest
from datetime import datetime, timedelta
from pathlib import Path

import cv2

from leafycv.config import load_config
from leafycv.monitor import render_monitor_preview


class MonitorPreviewTests(unittest.TestCase):
    def test_monitor_preview_renders_without_running_new_analysis(self):
        config = load_config(Path('configs/demo_normal.json'))
        frame = cv2.imread('demo/demo_normal.jpg')
        now = datetime.now().astimezone()
        result = {
            'analysis': {'visible_plant_count': 3, 'total_canopy_coverage': 16.4},
            'plants': [],
        }
        rendered = render_monitor_preview(frame, config, result, now, now + timedelta(minutes=30))
        self.assertEqual(rendered.shape, frame.shape)


if __name__ == '__main__':
    unittest.main()
