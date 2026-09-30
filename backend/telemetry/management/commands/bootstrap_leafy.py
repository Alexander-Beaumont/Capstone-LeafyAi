from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from telemetry.models import Camera, Farm, FarmDevice, FarmLevel
from sensor_ingest.services.configuration import bootstrap_environment_configuration


class Command(BaseCommand):
    help = "Create/update the LeafyAI lab farm, device, sensors, camera, and media directories."

    def handle(self, *args, **options):
        device_slug = str(settings.SENSOR_INGEST_DEVICE_SLUG or "").strip()
        if not device_slug:
            raise CommandError("SENSOR_INGEST_DEVICE_SLUG is required.")

        farm, _ = Farm.objects.get_or_create(
            name=settings.LEAFY_FARM_NAME,
            defaults={"location": settings.LEAFY_FARM_LOCATION or None},
        )
        if settings.LEAFY_FARM_LOCATION and farm.location != settings.LEAFY_FARM_LOCATION:
            farm.location = settings.LEAFY_FARM_LOCATION
            farm.save(update_fields=["location"])

        device, _ = FarmDevice.objects.get_or_create(
            slug=device_slug,
            defaults={
                "farm": farm,
                "name": settings.LEAFY_DEVICE_NAME,
                "device_type": settings.LEAFY_DEVICE_TYPE,
            },
        )
        changed = []
        if device.farm_id != farm.id:
            device.farm = farm
            changed.append("farm")
        if device.name != settings.LEAFY_DEVICE_NAME:
            device.name = settings.LEAFY_DEVICE_NAME
            changed.append("name")
        if device.device_type != settings.LEAFY_DEVICE_TYPE:
            device.device_type = settings.LEAFY_DEVICE_TYPE
            changed.append("device_type")
        if changed:
            device.save(update_fields=changed)

        call_command("seed_sensors", device_slug=device.slug)
        bootstrap_environment_configuration(device)

        level_number = settings.LEAFY_CAMERA_1_LEVEL
        if level_number not in (1, 2):
            raise CommandError("LEAFY_CAMERA_1_LEVEL must be 1 or 2.")

        levels = {}
        for number in (1, 2):
            levels[number], _ = FarmLevel.objects.get_or_create(
                device=device,
                level_number=number,
            )
        level = levels[level_number]

        if settings.LEAFY_CAMERA_1_IP:
            camera, _ = Camera.objects.get_or_create(
                farm_level=level,
                name=settings.LEAFY_CAMERA_1_NAME,
                defaults={
                    "source_type": "RTSP",
                    "ip_address": settings.LEAFY_CAMERA_1_IP,
                    "rtsp_port": settings.LEAFY_CAMERA_1_RTSP_PORT,
                    "rtsp_path": settings.LEAFY_CAMERA_1_RTSP_PATH,
                    "enabled": settings.LEAFY_CAMERA_1_ENABLED,
                    "capture_interval_minutes": settings.LEAFY_CAMERA_1_CAPTURE_INTERVAL_MINUTES,
                },
            )
            camera_updates = {
                "source_type": "RTSP",
                "ip_address": settings.LEAFY_CAMERA_1_IP,
                "rtsp_port": settings.LEAFY_CAMERA_1_RTSP_PORT,
                "rtsp_path": settings.LEAFY_CAMERA_1_RTSP_PATH,
                "enabled": settings.LEAFY_CAMERA_1_ENABLED,
                "capture_interval_minutes": settings.LEAFY_CAMERA_1_CAPTURE_INTERVAL_MINUTES,
            }
            changed_fields = []
            for field, value in camera_updates.items():
                if getattr(camera, field) != value:
                    setattr(camera, field, value)
                    changed_fields.append(field)
            if changed_fields:
                camera.save(update_fields=changed_fields)

        media_dir = Path(settings.MEDIA_ROOT) / "camera_images"
        media_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"LeafyAI bootstrap ready: farm={farm.id}, device={device.slug}, "
                f"camera_ip={settings.LEAFY_CAMERA_1_IP or 'not configured'}, "
                f"media={media_dir}."
            )
        )
