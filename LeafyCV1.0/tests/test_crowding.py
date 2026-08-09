from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cv"))

from crowding import adjacent_slot_pairs, compute_crowding


def two_slot_map(h=80, w=100):
    slot_map = np.zeros((h, w), dtype=np.int16)
    slot_map[:, w // 2:] = 1
    return slot_map


def test_adjacent_pairs():
    assert adjacent_slot_pairs(two_slot_map()) == [(0, 1)]


def test_no_contact():
    slots = two_slot_map()
    mask = np.zeros(slots.shape, dtype=np.uint8)
    mask[25:55, 15:30] = 255
    mask[25:55, 70:85] = 255
    result = compute_crowding(
        mask=mask, slot_map=slots, plant_count=2,
        gap_px=2, min_contact_pixels=10,
    )
    assert result["neighbor_pair_count"] == 1
    assert result["touching_pair_count"] == 0
    assert result["crowding_index"] == 0.0


def test_contact():
    slots = two_slot_map()
    mask = np.zeros(slots.shape, dtype=np.uint8)
    mask[20:60, 35:50] = 255
    mask[20:60, 50:65] = 255
    result = compute_crowding(
        mask=mask, slot_map=slots, plant_count=2,
        gap_px=2, min_contact_pixels=10,
    )
    assert result["touching_pair_count"] == 1
    assert result["crowding_index"] == 1.0
    assert result["per_plant_touching_neighbors"]["P1"] == ["P2"]
    assert result["per_plant_touching_neighbors"]["P2"] == ["P1"]


if __name__ == "__main__":
    test_adjacent_pairs()
    test_no_contact()
    test_contact()
    print("Crowding tests: OK")
