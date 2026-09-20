from django.test import TestCase

from leafy_runtime.bootstrap import ensure_default_farm_structure
from telemetry.models import Camera, Farm, FarmDevice, FarmLevel


class FarmStructureBootstrapTests(TestCase):
    def test_creates_two_levels_without_creating_camera(self):
        summary = ensure_default_farm_structure()

        self.assertEqual(Farm.objects.count(), 1)
        self.assertEqual(FarmDevice.objects.count(), 1)
        self.assertEqual(
            list(FarmLevel.objects.order_by("level_number").values_list("level_number", flat=True)),
            [1, 2],
        )
        self.assertEqual(Camera.objects.count(), 0)
        self.assertEqual(len(summary["level_ids"]), 2)

    def test_is_idempotent(self):
        first = ensure_default_farm_structure()
        second = ensure_default_farm_structure()

        self.assertEqual(Farm.objects.count(), 1)
        self.assertEqual(FarmDevice.objects.count(), 1)
        self.assertEqual(FarmLevel.objects.count(), 2)
        self.assertEqual(first["farm_id"], second["farm_id"])
        self.assertEqual(first["device_id"], second["device_id"])
        self.assertEqual(second["created"], [])

    def test_reuses_existing_farm_and_device(self):
        farm = Farm.objects.create(name="Existing Farm", location="Existing")
        device = FarmDevice.objects.create(
            farm=farm,
            name="Existing Rack",
            device_type="grow_rack",
        )

        summary = ensure_default_farm_structure()

        self.assertEqual(Farm.objects.count(), 1)
        self.assertEqual(FarmDevice.objects.count(), 1)
        self.assertEqual(summary["farm_id"], farm.id)
        self.assertEqual(summary["device_id"], device.id)
        self.assertEqual(FarmLevel.objects.filter(device=device).count(), 2)
