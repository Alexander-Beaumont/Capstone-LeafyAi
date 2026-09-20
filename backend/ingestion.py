from dataclasses import dataclass

from django.db import IntegrityError, transaction

from sensor_ingest.exceptions import IngestionConfigurationError, IngestionConflictError
from sensor_ingest.models import IngestionRecord
from telemetry.models import (
    ActuatorStateObservation,
    Sensor,
    SensorReading,
    SetpointObservation,
)


@dataclass(frozen=True)
class IngestionResult:
    created: bool
    duplicate: bool
    record_id: int
    source_entry_id: int
    status: str
    sensor_reading_count: int
    actuator_state_count: int
    setpoint_count: int
    missing_fields: tuple
    invalid_fields: tuple


def _existing_result(record):
    return IngestionResult(
        created=False,
        duplicate=True,
        record_id=record.id,
        source_entry_id=record.source_entry_id,
        status=record.status,
        sensor_reading_count=record.sensor_reading_count,
        actuator_state_count=record.actuator_state_count,
        setpoint_count=record.setpoint_count,
        missing_fields=tuple(record.missing_fields or []),
        invalid_fields=tuple(record.invalid_fields or []),
    )


@transaction.atomic
def ingest_snapshot(*, source_state, device, snapshot):
    """Persist one normalized source entry atomically and idempotently."""

    existing = (
        IngestionRecord.objects.select_for_update()
        .filter(source=source_state, source_entry_id=snapshot.entry_id)
        .first()
    )
    if existing is not None:
        if existing.payload_sha256 != snapshot.payload_sha256:
            raise IngestionConflictError(
                "ThingSpeak returned different payload content for an already "
                f"ingested entry_id={snapshot.entry_id}."
            )
        return _existing_result(existing)

    requested_slugs = tuple(snapshot.sensor_values.keys())
    sensors = Sensor.objects.filter(device=device, slug__in=requested_slugs)
    sensors_by_slug = {sensor.slug: sensor for sensor in sensors}

    missing_configuration = sorted(set(requested_slugs) - set(sensors_by_slug))
    if missing_configuration:
        raise IngestionConfigurationError(
            "Missing Sensor configuration for: " + ", ".join(missing_configuration)
        )

    sensor_count = 0
    for slug, normalized in snapshot.sensor_values.items():
        sensor = sensors_by_slug[slug]
        if not sensor.enabled:
            continue

        reading, created = SensorReading.objects.get_or_create(
            sensor=sensor,
            source="thingspeak",
            source_channel_id=source_state.external_source_id,
            source_entry_id=snapshot.entry_id,
            defaults={
                "value": normalized.value,
                "measured_at": snapshot.measured_at,
                "quality_status": normalized.quality_status,
                "quality_notes": normalized.quality_notes,
            },
        )
        if not created:
            if (
                reading.value != normalized.value
                or reading.measured_at != snapshot.measured_at
            ):
                raise IngestionConflictError(
                    f"SensorReading conflict for {slug} entry_id={snapshot.entry_id}."
                )
        else:
            sensor_count += 1

    actuator_count = 0
    if snapshot.irrigation_pump_state is not None:
        _, created = ActuatorStateObservation.objects.get_or_create(
            device=device,
            actuator_slug="irrigation_pump",
            source="thingspeak",
            source_channel_id=source_state.external_source_id,
            source_entry_id=snapshot.entry_id,
            defaults={
                "state": snapshot.irrigation_pump_state,
                "measured_at": snapshot.measured_at,
                "quality_status": "unverified",
            },
        )
        actuator_count = int(created)

    setpoint_count = 0
    if snapshot.target_ec is not None:
        _, created = SetpointObservation.objects.get_or_create(
            device=device,
            setpoint_slug="target_ec",
            source="thingspeak",
            source_channel_id=source_state.external_source_id,
            source_entry_id=snapshot.entry_id,
            defaults={
                "value": snapshot.target_ec.value,
                "unit": "µS/cm",
                "measured_at": snapshot.measured_at,
                "quality_status": snapshot.target_ec.quality_status,
                "quality_notes": snapshot.target_ec.quality_notes,
            },
        )
        setpoint_count = int(created)

    total_created = sensor_count + actuator_count + setpoint_count
    if total_created == 0:
        status = IngestionRecord.Status.EMPTY
    elif snapshot.missing_fields or snapshot.invalid_fields:
        status = IngestionRecord.Status.PARTIAL
    else:
        status = IngestionRecord.Status.COMPLETE

    try:
        # Use a nested savepoint so an IntegrityError caused by an accidental
        # second worker can be recovered without marking the outer transaction
        # as broken.
        with transaction.atomic():
            record = IngestionRecord.objects.create(
                source=source_state,
                source_entry_id=snapshot.entry_id,
                source_measured_at=snapshot.measured_at,
                payload_sha256=snapshot.payload_sha256,
                status=status,
                sensor_reading_count=sensor_count,
                actuator_state_count=actuator_count,
                setpoint_count=setpoint_count,
                missing_fields=list(snapshot.missing_fields),
                invalid_fields=list(snapshot.invalid_fields),
            )
    except IntegrityError as exc:
        # The database uniqueness constraint is the final protection if two
        # workers race.  Re-read and return the canonical record when content
        # is identical; otherwise surface a conflict.
        record = IngestionRecord.objects.filter(
            source=source_state,
            source_entry_id=snapshot.entry_id,
        ).first()
        if record and record.payload_sha256 == snapshot.payload_sha256:
            return _existing_result(record)
        raise IngestionConflictError(
            f"Concurrent ingestion conflict for entry_id={snapshot.entry_id}."
        ) from exc

    return IngestionResult(
        created=True,
        duplicate=False,
        record_id=record.id,
        source_entry_id=snapshot.entry_id,
        status=status,
        sensor_reading_count=sensor_count,
        actuator_state_count=actuator_count,
        setpoint_count=setpoint_count,
        missing_fields=snapshot.missing_fields,
        invalid_fields=snapshot.invalid_fields,
    )
