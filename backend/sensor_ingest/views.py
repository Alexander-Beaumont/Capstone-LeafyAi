from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from sensor_ingest.models import IngestionRecord, IngestionSourceState
from sensor_ingest.serializers import (
    IngestionRecordSerializer,
    IngestionSourceStateSerializer,
)
from sensor_ingest.services.health import source_health_dict


class IngestionSourceStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IngestionSourceState.objects.all().order_by("key")
    serializer_class = IngestionSourceStateSerializer


class IngestionRecordPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class IngestionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IngestionRecord.objects.select_related("source").order_by(
        "-source_measured_at", "-source_entry_id"
    )
    serializer_class = IngestionRecordSerializer
    pagination_class = IngestionRecordPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        source_key = self.request.query_params.get("source")
        if source_key:
            queryset = queryset.filter(source_id=source_key)
        return queryset


@api_view(["GET"])
def sensor_ingest_health(request):
    """Read-only operational health for configured telemetry sources."""

    sources = IngestionSourceState.objects.all().order_by("key")
    return Response(
        {
            "sources": [source_health_dict(source) for source in sources],
        }
    )
