from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.operation_locks import operation_lock
from core.pagination import OperatorLimitOffsetPagination
from sensor_ingest.exceptions import IngestionConfigurationError, SensorIngestError
from sensor_ingest.models import SensorIngestConfiguration
from sensor_ingest.serializers import SensorIngestConfigurationSerializer
from sensor_ingest.services.collector import SensorCollector
from sensor_ingest.services.runtime import perform_collection
from telemetry.models import Farm, FarmDevice


def _configuration(farm_id, device_id):
    get_object_or_404(Farm, id=farm_id)
    device = get_object_or_404(FarmDevice, id=device_id, farm_id=farm_id)
    return get_object_or_404(
        SensorIngestConfiguration.objects.select_related("device", "device__farm"),
        device=device,
    )


@api_view(["GET"])
def configuration_list(request, farm_id):
    get_object_or_404(Farm, id=farm_id)
    queryset = SensorIngestConfiguration.objects.filter(
        device__farm_id=farm_id
    ).select_related("device").order_by("device_id")
    paginator = OperatorLimitOffsetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = SensorIngestConfigurationSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET", "PATCH"])
def configuration_detail(request, farm_id, device_id):
    configuration = _configuration(farm_id, device_id)
    if request.method == "GET":
        return Response(SensorIngestConfigurationSerializer(configuration).data)
    serializer = SensorIngestConfigurationSerializer(
        configuration, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


def _operation(request, farm_id, device_id, *, store):
    configuration = _configuration(farm_id, device_id)
    if not configuration.enabled:
        return Response(
            {"detail": "Sensor ingestion is disabled for this device."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    lock = operation_lock("sensor-collect", device_id)
    if not lock.acquire(blocking=False):
        return Response(
            {"detail": "A collection is already running for this device."},
            status=status.HTTP_409_CONFLICT,
        )
    # Test performs the complete fetch/validation path without persistence;
    # Collect follows the same path and stores the resulting SensorReading rows.
    try:
        try:
            result = (
                perform_collection(configuration, store=True)
                if store else SensorCollector(configuration=configuration).collect(store=False)
            )
        except IngestionConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except SensorIngestError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:
            return Response(
                {"detail": f"Sensor endpoint operation failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        configuration.refresh_from_db()
        payload = result.as_dict()
        payload["validated"] = True
        payload["ingest_status"] = SensorIngestConfigurationSerializer(configuration).data
        return Response(payload)
    finally:
        lock.release()


@api_view(["POST"])
def test_configuration(request, farm_id, device_id):
    return _operation(request, farm_id, device_id, store=False)


@api_view(["POST"])
def collect_now(request, farm_id, device_id):
    return _operation(request, farm_id, device_id, store=True)
