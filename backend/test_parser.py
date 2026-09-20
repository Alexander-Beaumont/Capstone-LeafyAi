from django.test import SimpleTestCase

from sensor_ingest.exceptions import SourcePayloadError
from sensor_ingest.services.parser import parse_entry
from sensor_ingest.tests.fixtures import VALID_ENTRY


class ThingSpeakParserTests(SimpleTestCase):
    def test_valid_entry_preserves_identity_fields_and_hash(self):
        entry = parse_entry(VALID_ENTRY)
        self.assertEqual(entry.entry_id, 12345)
        self.assertEqual(entry.fields["field1"], "6.12")
        self.assertEqual(len(entry.payload_sha256), 64)
        self.assertIsNotNone(entry.measured_at.tzinfo)

    def test_unrelated_response_metadata_does_not_change_entry_hash(self):
        first = parse_entry(VALID_ENTRY)
        second = parse_entry(dict(VALID_ENTRY, latitude="-37.7", status="ok"))
        self.assertEqual(first.payload_sha256, second.payload_sha256)

    def test_missing_entry_id_rejected(self):
        payload = dict(VALID_ENTRY)
        payload.pop("entry_id")
        with self.assertRaises(SourcePayloadError):
            parse_entry(payload)

    def test_invalid_timestamp_rejected(self):
        payload = dict(VALID_ENTRY, created_at="not-a-date")
        with self.assertRaises(SourcePayloadError):
            parse_entry(payload)

    def test_naive_timestamp_rejected(self):
        payload = dict(VALID_ENTRY, created_at="2026-09-06T10:30:00")
        with self.assertRaises(SourcePayloadError):
            parse_entry(payload)
