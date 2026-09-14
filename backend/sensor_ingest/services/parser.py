import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from sensor_ingest.exceptions import SourcePayloadError


FIELD_NAMES = tuple(f"field{number}" for number in range(1, 9))


@dataclass(frozen=True)
class ThingSpeakEntry:
    entry_id: int
    measured_at: datetime
    fields: Dict[str, Optional[str]]
    payload_sha256: str


def _canonical_payload_hash(payload):
    # Hash only the source fields Leafy AI treats as the entry contract.  This
    # avoids false conflicts if ThingSpeak adds unrelated response metadata.
    relevant = {
        "entry_id": payload.get("entry_id"),
        "created_at": payload.get("created_at"),
        **{name: payload.get(name) for name in FIELD_NAMES},
    }
    canonical = json.dumps(
        relevant,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_entry(payload):
    """Validate entry identity/chronology while preserving field values.

    Individual field validation belongs to the mapper so one malformed field
    cannot cause otherwise-good measurements in the same entry to be lost.
    """

    if not isinstance(payload, dict):
        raise SourcePayloadError("ThingSpeak entry must be a JSON object.")

    raw_entry_id = payload.get("entry_id")
    try:
        entry_id = int(raw_entry_id)
    except (TypeError, ValueError) as exc:
        raise SourcePayloadError("ThingSpeak entry_id is missing or invalid.") from exc
    if entry_id <= 0:
        raise SourcePayloadError("ThingSpeak entry_id must be positive.")

    raw_created_at = payload.get("created_at")
    if not isinstance(raw_created_at, str) or not raw_created_at.strip():
        raise SourcePayloadError("ThingSpeak created_at is missing or invalid.")

    measured_at = parse_datetime(raw_created_at.strip())
    if measured_at is None:
        raise SourcePayloadError("ThingSpeak created_at is not a valid ISO timestamp.")
    if timezone.is_naive(measured_at):
        raise SourcePayloadError("ThingSpeak created_at must include a timezone.")

    fields = {name: payload.get(name) for name in FIELD_NAMES}

    return ThingSpeakEntry(
        entry_id=entry_id,
        measured_at=measured_at,
        fields=fields,
        payload_sha256=_canonical_payload_hash(payload),
    )
