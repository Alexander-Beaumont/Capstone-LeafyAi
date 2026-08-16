import unittest
import numpy as np

from leafycv.crowding import adjacent_slot_pairs, compute_crowding


def two_slot_map(h=80, w=100):
    slot_map = np.zeros((h, w), dtype=np.int16)
    slot_map[:, w // 2:] = 1
    return slot_map


class CrowdingTests(unittest.TestCase):
    def test_adjacent_pairs(self):
        self.assertEqual(adjacent_slot_pairs(two_slot_map()), [(0, 1)])

    def test_no_contact(self):
        slots = two_slot_map()
        mask = np.zeros(slots.shape, dtype=np.uint8)
        mask[25:55, 15:30] = 255
        mask[25:55, 70:85] = 255
        result = compute_crowding(mask=mask, slot_map=slots, plant_count=2, gap_px=2, min_contact_pixels=10)
        self.assertEqual(result["touching_pair_count"], 0)

    def test_contact(self):
        slots = two_slot_map()
        mask = np.zeros(slots.shape, dtype=np.uint8)
        mask[20:60, 35:50] = 255
        mask[20:60, 50:65] = 255
        result = compute_crowding(mask=mask, slot_map=slots, plant_count=2, gap_px=2, min_contact_pixels=10)
        self.assertEqual(result["touching_pair_count"], 1)
        self.assertEqual(result["crowding_index"], 1.0)


if __name__ == "__main__":
    unittest.main()
