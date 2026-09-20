from rest_framework import serializers

from sensor_ingest.models import IngestionRecord, IngestionSourceState


class IngestionSourceStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionSourceState
        fields = [
            "key",
            "provider",
            "external_source_id",
            "last_attempt_at",
            "last_http_success_at",
            "last_new_entry_at",
            "last_source_entry_id",
            "last_source_measured_at",
            "consecutive_failures",
            "last_error_code",
            "last_error_message",
            "updated_at",
        ]
        read_only_fields = fields


class IngestionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionRecord
        fields = [
            "id",
            "source",
            "source_entry_id",
            "source_measured_at",
            "status",
            "sensor_reading_count",
            "actuator_state_count",
            "setpoint_count",
            "missing_fields",
            "invalid_fields",
            "ingested_at",
        ]
        read_only_fields = fields
