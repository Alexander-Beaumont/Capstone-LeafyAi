"""Seed only non-camera infrastructure required to configure the app.

This command intentionally creates ZERO Camera rows. Plant Vision remains empty
until a user explicitly adds a Camera through the UI/API.
"""
from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from telemetry.models import Farm, FarmDevice, FarmLevel, Sensor


class Command(BaseCommand):
    help = "Create farm levels/sensor identities without creating a Camera."

    def handle(self, *args, **options):
        farm, _ = Farm.objects.get_or_create(
            name=os.getenv("LEAFY_FARM_NAME", "LeafyAI Farm"),
            defaults={"location": os.getenv("LEAFY_FARM_LOCATION", "")},
        )
        rack, _ = FarmDevice.objects.get_or_create(
            farm=farm,
            name=os.getenv("LEAFY_RACK_NAME", "LeafyAI Grow Rack"),
            defaults={"device_type": "grow_rack"},
        )
        level1, _ = FarmLevel.objects.get_or_create(device=rack, level_number=1)
        level2, _ = FarmLevel.objects.get_or_create(device=rack, level_number=2)

        sensor_defs = [
            ("ph", "pH"),
            ("ec", "mS/cm"),
            ("water_temp", "°C"),
            ("ambient_temp", "°C"),
            ("humidity", "%"),
            ("dew_point", "°C"),
            ("water_level", "%"),
        ]
        for sensor_type, unit in sensor_defs:
            Sensor.objects.get_or_create(
                device=rack,
                sensor_type=sensor_type,
                defaults={"unit": unit},
            )

        username = os.getenv("LEAFY_BOOTSTRAP_USERNAME", "").strip()
        password = os.getenv("LEAFY_BOOTSTRAP_PASSWORD", "")
        if username and password:
            User = get_user_model()
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": os.getenv("LEAFY_BOOTSTRAP_EMAIL", "")},
            )
            # Compose workers must always be able to authenticate with the current
            # configured service credentials, including after an existing volume is reused.
            changed_fields = []
            email = os.getenv("LEAFY_BOOTSTRAP_EMAIL", "")
            if email and user.email != email:
                user.email = email
                changed_fields.append("email")
            if not user.check_password(password):
                user.set_password(password)
                changed_fields.append("password")
            if changed_fields:
                user.save(update_fields=changed_fields)
            action = "Created" if created else "Synchronized"
            self.stdout.write(f"{action} bootstrap user: {username}")

        from telemetry.models import Camera
        camera_count = Camera.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Base metadata ready: Farm {farm.id}, levels {level1.id}/{level2.id}. Camera count: {camera_count}."
        ))
