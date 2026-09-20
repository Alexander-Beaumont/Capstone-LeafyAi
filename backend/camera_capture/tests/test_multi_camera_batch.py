import numpy as np

from camera_capture.camera_collector import CameraCollector


class FakeBackend:
    def __init__(self):
        self.uploaded = []

    def get_cameras(self):
        return [
            {
                "id": 1,
                "enabled": True,
                "cv_enabled": True,
                "capture_interval_minutes": 30,
                "active_start_time": None,
                "active_end_time": None,
            },
            {
                "id": 2,
                "enabled": True,
                "cv_enabled": True,
                "capture_interval_minutes": 60,
                "active_start_time": None,
                "active_end_time": None,
            },
        ]

    def get_latest_image(self, camera_id):
        return None

    def upload_official_image(self, camera_id, jpeg_bytes, *, captured_at, quality):
        self.uploaded.append(camera_id)
        return {"image_id": 100 + camera_id, "camera_id": camera_id}


def test_two_due_cameras_are_captured_in_one_poll(monkeypatch):
    backend = FakeBackend()

    monkeypatch.setattr(
        "camera_capture.camera_collector.capture_fresh_frame",
        lambda camera, **kwargs: np.zeros((10, 20, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(
        "camera_capture.camera_collector.encode_jpeg",
        lambda frame, jpeg_quality=92: b"jpeg",
    )

    collector = CameraCollector(backend)

    assert collector.process_all() == 2
    assert backend.uploaded == [1, 2]
