from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sensor_ingest.services.configuration import ensure_sensor_definitions
from telemetry.models import FarmDevice


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

        created_count, updated_count = ensure_sensor_definitions(
            device,
            force_timing=options["force_timing"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sensor configuration ready for {device.slug}: "
                f"created={created_count}, updated={updated_count}."
            )
        )
