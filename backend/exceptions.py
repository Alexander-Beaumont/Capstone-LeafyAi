class SensorIngestError(Exception):
    """Base class for controlled sensor-ingestion failures."""

    code = "sensor_ingest_error"


class SourceTransportError(SensorIngestError):
    code = "source_transport_error"


class SourceAuthenticationError(SensorIngestError):
    code = "source_authentication_error"


class SourcePayloadError(SensorIngestError):
    code = "source_payload_error"


class IngestionConfigurationError(SensorIngestError):
    code = "ingestion_configuration_error"


class IngestionConflictError(SensorIngestError):
    code = "ingestion_conflict"
