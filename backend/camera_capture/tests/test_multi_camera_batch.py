from datetime import datetime

import numpy as np

from camera_capture.camera_collector import CameraCollector
from camera_capture.lighting_client import LightingResult


class FakeBackend:
    def __init__(self):
        self.uploaded = []

    def get_cameras(self):
        return [
            {
                "id": 1,
                "enabled": True,
                "capture_interval_minutes": 30,
                "active_start_time": None,
                "active_end_time": None,
            },
            {
                "id": 2,
                "enabled": True,
                "capture_interval_minutes": 60,
                "active_start_time": None,
                "active_end_time": None,
            },
        ]

    def get_latest_image(self, camera_id):
        return None

    def upload_official_image(
        self,
        camera_id,
        jpeg_bytes,
        *,
        captured_at,
        quality,
    ):
        self.uploaded.append(
            camera_id
        )

        return {
            "image_id": 100 + camera_id,
            "camera_id": camera_id,
        }


class FakeLighting:
    def __init__(self, initial="OFF"):
        self.calls = []
        self.state = initial

    def get_state(self):
        return LightingResult(True, self.state)

    def set_state(self, state):
        self.calls.append(state)
        self.state = state
        return LightingResult(True, state)


def test_two_due_cameras_share_one_lighting_cycle(monkeypatch):
    backend = FakeBackend()
    lighting = FakeLighting()
    sleeps = []

    monkeypatch.setattr(
        "camera_capture.camera_collector.capture_fresh_frame",
        lambda camera, **kwargs: np.zeros((10, 20, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(
        "camera_capture.camera_collector.encode_jpeg",
        lambda frame, jpeg_quality=92: b"jpeg",
    )

    collector = CameraCollector(
        backend,
        lighting=lighting,
        pre_capture_light_on_seconds=2.0,
        post_capture_restore_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    assert collector.process_all() == 2
    assert lighting.calls == ["ON", "OFF"]
    assert sleeps == [2.0, 1.0]
    assert backend.uploaded == [1, 2]
