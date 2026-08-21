from pathlib import Path


def test_removed_modules_not_present():
    root = Path(__file__).resolve().parents[1] / "leafycv"
    for name in ["camera.py", "slots.py", "calibration.py", "monitor.py", "gui.py"]:
        assert not (root / name).exists()
