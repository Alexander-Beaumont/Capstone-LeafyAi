import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sensor_ingest.exceptions import SensorIngestError
from sensor_ingest.services.collector import SensorCollector


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Continuously collect Leafy AI telemetry from ThingSpeak."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run one collection cycle and exit; startup backfill still runs unless --no-backfill.",
        )
        parser.add_argument(
            "--no-backfill",
            action="store_true",
            help="Skip startup history reconciliation.",
        )
        parser.add_argument(
            "--backfill",
            type=int,
            default=None,
            help="Number of recent ThingSpeak entries to reconcile at startup.",
        )
        parser.add_argument("--poll-seconds", type=int, default=None)
        parser.add_argument("--reconcile-seconds", type=int, default=None)

    def handle(self, *args, **options):
        poll_seconds = options["poll_seconds"] or int(
            settings.SENSOR_INGEST_POLL_SECONDS
        )
        reconcile_seconds = options["reconcile_seconds"] or int(
            settings.SENSOR_INGEST_RECONCILE_SECONDS
        )
        backfill_results = options["backfill"] or int(
            settings.SENSOR_INGEST_BACKFILL_RESULTS
        )

        if poll_seconds <= 0:
            raise CommandError("--poll-seconds must be greater than zero.")
        if reconcile_seconds <= 0:
            raise CommandError("--reconcile-seconds must be greater than zero.")
        if not 1 <= backfill_results <= 8000:
            raise CommandError("--backfill must be between 1 and 8000.")

        collector = SensorCollector()
        try:
            collector.validate_configuration()
        except SensorIngestError as exc:
            raise CommandError(str(exc)) from exc

        if not options["no_backfill"]:
            try:
                summary = collector.reconcile(results=backfill_results)
                self.stdout.write(
                    self.style.SUCCESS(f"Startup reconciliation: {summary}")
                )
            except SensorIngestError as exc:
                # Historical backfill failure should not permanently prevent the
                # daemon from starting; latest polling can recover and the next
                # periodic reconciliation will retry history.
                self.stderr.write(
                    self.style.WARNING(f"Startup reconciliation failed: {exc}")
                )

        if options["once"]:
            try:
                result = collector.collect_latest()
            except SensorIngestError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(
                self.style.SUCCESS(
                    f"Latest entry processed: entry_id={result.source_entry_id} "
                    f"status={result.status} created={result.created}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Leafy AI sensor collector started; poll={poll_seconds}s, "
                f"reconcile={reconcile_seconds}s."
            )
        )

        last_reconcile = time.monotonic()
        try:
            while True:
                sleep_seconds = poll_seconds
                try:
                    collector.collect_latest()
                    now = time.monotonic()
                    if now - last_reconcile >= reconcile_seconds:
                        collector.reconcile(results=backfill_results)
                        last_reconcile = now
                except SensorIngestError as exc:
                    failures = max(1, collector.source_state.consecutive_failures)
                    base = int(settings.SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS)
                    maximum = int(settings.SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS)
                    sleep_seconds = min(maximum, base * (2 ** (failures - 1)))
                    logger.warning(
                        "Sensor collection failed (%s); retrying in %ss.",
                        exc,
                        sleep_seconds,
                    )
                except Exception:
                    logger.exception("Unexpected sensor collector error.")
                    sleep_seconds = int(
                        settings.SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS
                    )

                time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            self.stdout.write("Sensor collector stopped.")
