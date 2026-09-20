import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sensor_ingest.exceptions import SensorIngestError
from sensor_ingest.services.collector import SensorCollector


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Continuously collect Leafy AI telemetry from local sensor devices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run one local sensor collection cycle and exit.",
        )
        parser.add_argument(
            "--poll-seconds",
            type=int,
            default=None,
            help="Override the configured sensor polling interval.",
        )

    def handle(self, *args, **options):
        poll_seconds = (
            options["poll_seconds"]
            or int(settings.SENSOR_INGEST_POLL_SECONDS)
        )

        if poll_seconds <= 0:
            raise CommandError(
                "--poll-seconds must be greater than zero."
            )

        collector = SensorCollector()

        try:
            collector.validate_configuration()
        except SensorIngestError as exc:
            raise CommandError(str(exc)) from exc

        if options["once"]:
            try:
                count = collector.collect_latest()
            except SensorIngestError as exc:
                raise CommandError(str(exc)) from exc

            self.stdout.write(
                self.style.SUCCESS(
                    f"Sensor cycle complete: "
                    f"stored={count} reading(s)."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                "Leafy AI local sensor collector started; "
                f"poll={poll_seconds}s."
            )
        )

        failures = 0

        try:
            while True:
                sleep_seconds = poll_seconds

                try:
                    count = collector.collect_latest()
                    failures = 0

                    logger.info(
                        "Sensor collection cycle complete: "
                        "stored=%s",
                        count,
                    )

                except SensorIngestError as exc:
                    failures += 1

                    base = int(
                        settings
                        .SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS
                    )
                    maximum = int(
                        settings
                        .SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS
                    )

                    sleep_seconds = min(
                        maximum,
                        base * (2 ** (failures - 1)),
                    )

                    logger.warning(
                        "Sensor collection failed (%s); "
                        "retrying in %ss.",
                        exc,
                        sleep_seconds,
                    )

                except Exception:
                    failures += 1

                    logger.exception(
                        "Unexpected sensor collector error."
                    )

                    sleep_seconds = int(
                        settings
                        .SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS
                    )

                time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            self.stdout.write(
                "Sensor collector stopped."
            )