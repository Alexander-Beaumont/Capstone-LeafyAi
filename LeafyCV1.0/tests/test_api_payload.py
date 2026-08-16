import unittest

from leafycv.api import build_backend_payload


class ApiPayloadTests(unittest.TestCase):
    def test_uuid_slot_id_and_nullable_magenta_values(self):
        result = {
            "camera_name": "My Camera",
            "captured_at": "2026-08-15T14:00:00+10:00",
            "lighting_mode": "MAGENTA",
            "size_calibrated": False,
            "colour_measurement_valid": False,
            "analysis": {
                "total_canopy_coverage": 42.5,
                "visible_plant_count": 1,
                "measurement_valid": True,
                "processing_time_ms": 100,
            },
            "plants": [
                {
                    "slot_id": "550e8400-e29b-41d4-a716-446655440000",
                    "canopy_coverage": 42.5,
                    "width_px": 300.0,
                    "height_px": 250.0,
                    "width_cm": None,
                    "height_cm": None,
                    "green_percentage": None,
                    "yellow_percentage": None,
                    "crowding_percentage": 50.0,
                    "growth_change": 2.5,
                    "visible": True,
                    "measurement_valid": True,
                }
            ],
        }
        payload = build_backend_payload(result)
        plant = payload["plants"][0]
        self.assertEqual(plant["slot_id"], "550e8400-e29b-41d4-a716-446655440000")
        self.assertIsNone(plant["width_cm"])
        self.assertIsNone(plant["green_percentage"])
        self.assertFalse(payload["colour_measurement_valid"])


if __name__ == "__main__":
    unittest.main()
