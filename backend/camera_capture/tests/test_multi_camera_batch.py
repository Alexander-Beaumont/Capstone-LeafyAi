import numpy as np

from camera_capture.camera_collector import CameraCollector


class FakeBackend:
    def __init__(self):
        self.uploaded = []

    def get_cameras(self):
        return [
            {"id": 1, "enabled": True, "capture_interval_minutes": 30, "active_start_time": None, "active_end_time": None},
            {"id": 2, "enabled": True, "capture_interval_minutes": 60, "active_start_time": None, "active_end_time": None},
        ]

    def get_latest_image(self, camera_id):
        return None

    def upload_official_image(self, camera_id, jpeg_bytes, *, captured_at, quality):
        self.uploaded.append((camera_id, quality["quality_status"], quality["vlm_ready"]))
        return {"image_id": 100 + camera_id, "camera_id": camera_id}


def test_two_due_cameras_capture_without_lighting_control(monkeypatch):
    backend = FakeBackend()
    # Textured frame avoids blur/contrast rejection and is large enough for quality checks.
    frame = np.indices((480, 640)).sum(axis=0).astype(np.uint8)
    frame = np.stack([frame, np.roll(frame, 11, 1), np.roll(frame, 23, 0)], axis=2)

    monkeypatch.setattr("camera_capture.camera_collector.capture_fresh_frame", lambda camera, **kwargs: frame)
    monkeypatch.setattr("camera_capture.camera_collector.encode_jpeg", lambda frame, jpeg_quality=92: b"jpeg")

    collector = CameraCollector(backend)
    assert collector.process_all() == 2
    assert [row[0] for row in backend.uploaded] == [1, 2]
    assert all(row[1] in {"PASS", "FAIL"} for row in backend.uploaded)
