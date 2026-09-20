from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sensor_ingest.services.mapper import SENSOR_DEFINITIONS
from telemetry.models import FarmDevice, Sensor


class Command(BaseCommand):
    help = "Create/update the Leafy AI physical sensor definitions."

    def add_arguments(self, parser):
        parser.add_argument("--device-slug", default=None)
        parser.add_argument(
            "--force-timing",
            action="store_true",
            help="Overwrite timing settings on existing sensor rows.",
        )

    def handle(self, *args, **options):
        device_slug = options["device_slug"] or settings.SENSOR_INGEST_DEVICE_SLUG
        if not device_slug:
            raise CommandError(
                "Set SENSOR_INGEST_DEVICE_SLUG or pass --device-slug."
            )

        try:
            device = FarmDevice.objects.get(slug=device_slug)
        except FarmDevice.DoesNotExist as exc:
            raise CommandError(
                f"FarmDevice slug '{device_slug}' does not exist."
            ) from exc

        expected = int(settings.SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS)
        stale = int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS)

        created_count = 0
        updated_count = 0
        for definition in SENSOR_DEFINITIONS:
            defaults = {
                "sensor_type": definition.sensor_type,
                "unit": definition.unit,
                "enabled": True,
                "expected_interval_seconds": expected,
                "stale_after_seconds": stale,
            }
            sensor, created = Sensor.objects.get_or_create(
                device=device,
                slug=definition.slug,
                defaults=defaults,
            )
            if created:
                created_count += 1
                continue

            changed = False
            if sensor.sensor_type != definition.sensor_type:
                sensor.sensor_type = definition.sensor_type
                changed = True
            if sensor.unit != definition.unit:
                sensor.unit = definition.unit
                changed = True
            if options["force_timing"]:
                if sensor.expected_interval_seconds != expected:
                    sensor.expected_interval_seconds = expected
                    changed = True
                if sensor.stale_after_seconds != stale:
                    sensor.stale_after_seconds = stale
                    changed = True
            if changed:
                sensor.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sensor configuration ready for {device.slug}: "
                f"created={created_count}, updated={updated_count}."
            )
        )
