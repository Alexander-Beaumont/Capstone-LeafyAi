from collections import defaultdict
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ai_agent.models import AIConfiguration, AIRecommendationRun
from ai_agent.scheduler import next_eligible_time
from ai_agent.serializers import AIRecommendationRunSerializer
from camera_capture.services import build_collector
from core.operation_locks import operation_lock
from core.pagination import OperatorLimitOffsetPagination
from farm_state.services import build_farm_state
from sensor_ingest.models import SensorIngestConfiguration
from telemetry.models import Camera, CameraImage, Farm, SensorReading
from telemetry.operator_serializers import FarmCameraSerializer, OperatorCameraImageSerializer
from telemetry.serializers import CameraImageSerializer, CameraSerializer, FarmSerializer, SensorReadingSerializer


def _farm(farm_id):
    return get_object_or_404(Farm, id=farm_id)


def _datetime_parameter(request, name):
    aliases = {
        "start": ("start", "start_at", "date_from"),
        "end": ("end", "end_at", "date_to"),
    }
    value = next(
        (request.query_params.get(key) for key in aliases.get(name, (name,)) if request.query_params.get(key)),
        None,
    )
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise serializers.ValidationError({name: "Use an ISO 8601 date-time."})
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _csv(value):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _integer_csv(value, field):
    values = _csv(value)
    try:
        return [int(item) for item in values]
    except ValueError as exc:
        raise serializers.ValidationError({field: "Use comma-separated integer IDs."}) from exc


def _boolean_parameter(request, name):
    value = request.query_params.get(name)
    if value is None:
        return None
    if value.lower() in {"1", "true", "yes"}:
        return True
    if value.lower() in {"0", "false", "no"}:
        return False
    raise serializers.ValidationError({name: "Use true or false."})


@api_view(["GET"])
def sensor_readings(request, farm_id):
    _farm(farm_id)
    queryset = SensorReading.objects.filter(
        sensor__device__farm_id=farm_id
    ).select_related("sensor").order_by("-measured_at", "-id")
    sensor_slugs = _csv(request.query_params.get("sensor") or request.query_params.get("sensors"))
    quality = _csv(request.query_params.get("quality"))
    start = _datetime_parameter(request, "start")
    end = _datetime_parameter(request, "end")
    if sensor_slugs:
        queryset = queryset.filter(sensor__slug__in=sensor_slugs)
    if request.query_params.get("sensor_id"):
        sensor_ids = _integer_csv(request.query_params["sensor_id"], "sensor_id")
        queryset = queryset.filter(sensor_id__in=sensor_ids)
    if quality:
        queryset = queryset.filter(quality_status__in=quality)
    if start:
        queryset = queryset.filter(measured_at__gte=start)
    if end:
        queryset = queryset.filter(measured_at__lte=end)
    paginator = OperatorLimitOffsetPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(
        SensorReadingSerializer(page, many=True).data
    )


def _history_range(request):
    preset = request.query_params.get("preset", "24h")
    now = timezone.now()
    presets = {
        "1h": (timedelta(hours=1), 300),
        "24h": (timedelta(hours=24), 900),
        "7d": (timedelta(days=7), 3600),
    }
    if preset == "custom":
        start = _datetime_parameter(request, "start")
        end = _datetime_parameter(request, "end") or now
        if start is None:
            raise serializers.ValidationError({"start": "start is required for a custom range."})
        default_bucket = 900
    elif preset in presets:
        delta, default_bucket = presets[preset]
        start, end = now - delta, now
    else:
        raise serializers.ValidationError({"preset": "Use 1h, 24h, 7d, or custom."})
    if start >= end:
        raise serializers.ValidationError({"end": "end must be later than start."})
    raw_bucket = request.query_params.get("bucket_seconds") or request.query_params.get("bucket")
    duration_buckets = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "6h": 21600, "1d": 86400}
    try:
        bucket = (
            duration_buckets[raw_bucket]
            if raw_bucket in duration_buckets
            else int(raw_bucket)
        ) if raw_bucket else default_bucket
    except ValueError as exc:
        raise serializers.ValidationError({"bucket_seconds": "Use a whole number of seconds."}) from exc
    if bucket < 60 or bucket > 86400:
        raise serializers.ValidationError({"bucket_seconds": "Use a value from 60 to 86400."})
    return preset, start, end, bucket


@api_view(["GET"])
def sensor_history(request, farm_id):
    _farm(farm_id)
    preset, start, end, bucket_seconds = _history_range(request)
    slugs = _csv(request.query_params.get("sensors") or request.query_params.get("sensor"))
    queryset = SensorReading.objects.filter(
        sensor__device__farm_id=farm_id,
        measured_at__gte=start,
        measured_at__lte=end,
    ).select_related("sensor").order_by("measured_at", "id")
    if slugs:
        queryset = queryset.filter(sensor__slug__in=slugs)
    buckets = defaultdict(list)
    origin = start.timestamp()
    for reading in queryset:
        index = int((reading.measured_at.timestamp() - origin) // bucket_seconds)
        buckets[(reading.sensor_id, index)].append(reading)
    sensors = {}
    for readings in buckets.values():
        sensor = readings[0].sensor
        entry = sensors.setdefault(sensor.id, {
            "sensor_id": sensor.id,
            "sensor_slug": sensor.slug,
            "sensor_type": sensor.sensor_type,
            "unit": sensor.unit,
            "points": [],
        })
        values = [float(item.value) for item in readings]
        latest = max(readings, key=lambda item: (item.measured_at, item.id))
        index = int((readings[0].measured_at.timestamp() - origin) // bucket_seconds)
        entry["points"].append({
            "timestamp": start + timedelta(seconds=index * bucket_seconds),
            "minimum": min(values),
            "maximum": max(values),
            "average": sum(values) / len(values),
            "latest": float(latest.value),
            "sample_count": len(values),
        })
    return Response({
        "preset": preset,
        "start": start,
        "end": end,
        "bucket_seconds": bucket_seconds,
        "series": sorted(sensors.values(), key=lambda item: item["sensor_id"]),
    })


def _camera_queryset(farm_id):
    return Camera.objects.filter(
        farm_level__device__farm_id=farm_id
    ).select_related("farm_level", "farm_level__device").order_by("id")


@api_view(["GET", "POST"])
def cameras(request, farm_id):
    farm = _farm(farm_id)
    if request.method == "POST":
        serializer = FarmCameraSerializer(data=request.data, context={"request": request, "farm": farm})
        serializer.is_valid(raise_exception=True)
        camera = serializer.save()
        return Response(
            FarmCameraSerializer(camera, context={"request": request, "farm": farm}).data,
            status=status.HTTP_201_CREATED,
        )
    queryset = _camera_queryset(farm_id).filter(is_archived=False)
    paginator = OperatorLimitOffsetPagination()
    page = paginator.paginate_queryset(queryset, request)
    data = FarmCameraSerializer(page, many=True, context={"request": request, "farm": farm}).data
    return paginator.get_paginated_response(data)


@api_view(["GET", "PATCH"])
def camera_detail(request, farm_id, camera_id):
    farm = _farm(farm_id)
    camera = get_object_or_404(_camera_queryset(farm_id), id=camera_id)
    if request.method == "PATCH":
        serializer = FarmCameraSerializer(
            camera, data=request.data, partial=True,
            context={"request": request, "farm": farm},
        )
        serializer.is_valid(raise_exception=True)
        camera = serializer.save()
    return Response(FarmCameraSerializer(camera, context={"request": request, "farm": farm}).data)


@api_view(["POST"])
def capture_camera(request, farm_id, camera_id):
    farm = _farm(farm_id)
    camera = get_object_or_404(_camera_queryset(farm_id), id=camera_id)
    if camera.is_archived or not camera.enabled:
        return Response(
            {"detail": "Disabled or archived cameras cannot capture."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    camera_payload = CameraSerializer(camera).data
    validator = CameraSerializer(data=camera_payload)
    if not validator.is_valid():
        return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)
    lock = operation_lock("camera-capture", camera_id)
    if not lock.acquire(blocking=False):
        return Response(
            {"detail": "A capture is already running for this camera."},
            status=status.HTTP_409_CONFLICT,
        )
    try:
        try:
            captured = build_collector().process_camera(
                camera_payload,
                force=True,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Camera capture failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not captured:
            return Response(
                {"detail": "Camera capture did not produce an image."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        image = CameraImage.objects.filter(camera=camera).order_by("-captured_at", "-id").first()
        return Response(
            CameraImageSerializer(image, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    finally:
        lock.release()


@api_view(["GET"])
def camera_images(request, farm_id):
    _farm(farm_id)
    queryset = CameraImage.objects.filter(
        camera__farm_level__device__farm_id=farm_id
    ).select_related("camera").order_by("-captured_at", "-id")
    camera_ids = _integer_csv(
        request.query_params.get("camera") or request.query_params.get("cameras"),
        "camera",
    )
    qualities = _csv(request.query_params.get("quality") or request.query_params.get("quality_status"))
    start = _datetime_parameter(request, "start")
    end = _datetime_parameter(request, "end")
    vlm_ready = _boolean_parameter(request, "vlm_ready")
    ai_used = _boolean_parameter(request, "ai_used")
    if camera_ids:
        queryset = queryset.filter(camera_id__in=camera_ids)
    if qualities:
        queryset = queryset.filter(quality_status__in=[value.upper() for value in qualities])
    if start:
        queryset = queryset.filter(captured_at__gte=start)
    if end:
        queryset = queryset.filter(captured_at__lte=end)
    if vlm_ready is not None:
        queryset = queryset.filter(vlm_ready=vlm_ready)
    if ai_used is True:
        queryset = queryset.filter(ai_recommendation_runs__isnull=False).distinct()
    elif ai_used is False:
        queryset = queryset.filter(ai_recommendation_runs__isnull=True)
    paginator = OperatorLimitOffsetPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(
        OperatorCameraImageSerializer(page, many=True, context={"request": request}).data
    )


@api_view(["GET"])
def dashboard(request, farm_id):
    farm = _farm(farm_id)
    now = timezone.now()
    farm_state = build_farm_state(farm)
    sensor_states = [
        sensor
        for device in farm_state["devices"]
        for sensor in device["sensors"]
        if sensor["enabled"]
    ]
    sensor_counts = {
        "total": len(sensor_states),
        "fresh": sum(item["status"] == "fresh" for item in sensor_states),
        "stale": sum(item["status"] == "stale" for item in sensor_states),
        "missing": sum(item["status"] == "missing" for item in sensor_states),
        "suspect": sum(item.get("quality_status") == "suspect" for item in sensor_states),
    }
    ingest = list(SensorIngestConfiguration.objects.filter(
        device__farm=farm
    ).select_related("device").order_by("device_id"))
    if not ingest:
        ingest_state = "not_configured"
    elif not any(item.enabled for item in ingest):
        ingest_state = "disabled"
    elif any(item.last_error for item in ingest if item.enabled):
        ingest_state = "error"
    else:
        ingest_state = "healthy"
    last_success = max((item.last_success_at for item in ingest if item.last_success_at), default=None)
    camera_qs = _camera_queryset(farm_id).filter(is_archived=False)
    latest_image = CameraImage.objects.filter(
        camera__in=camera_qs
    ).select_related("camera").order_by("-captured_at", "-id").first()
    camera_data = FarmCameraSerializer(
        camera_qs, many=True, context={"request": request, "farm": farm}
    ).data
    next_capture = min(
        (item["next_scheduled_capture"] for item in camera_data if item["next_scheduled_capture"]),
        default=None,
    )
    configuration, _ = AIConfiguration.objects.get_or_create(farm=farm)
    latest_run = AIRecommendationRun.objects.filter(farm=farm).first()
    latest_run_data = (
        AIRecommendationRunSerializer(latest_run, context={"request": request}).data
        if latest_run else None
    )
    recommendations = latest_run.recommendations.all() if latest_run else []
    action_count = sum(item.actions.count() for item in recommendations)
    return Response({
        "farm": FarmSerializer(farm).data,
        "generated_at": now,
        "sensors": {
            "counts": sensor_counts,
            "ingestion_status": ingest_state,
            "last_successful_collection": last_success,
            "devices": len(ingest),
        },
        "cameras": {
            "count": camera_qs.count(),
            "latest_image": CameraImageSerializer(latest_image, context={"request": request}).data if latest_image else None,
            "image_quality": ({
                "status": latest_image.quality_status,
                "flags": latest_image.quality_flags,
                "message": latest_image.quality_message,
                "vlm_ready": latest_image.vlm_ready,
            } if latest_image else None),
            "next_capture": next_capture,
        },
        "ai": {
            "schedule_state": "enabled" if configuration.schedule_enabled else "disabled",
            "next_eligible_window": next_eligible_time(configuration, now) if configuration.schedule_enabled else None,
            "latest_run": latest_run_data,
            "action_summary": {
                "recommendations": len(recommendations),
                "automatic": sum(item.execution_type == "automated" for item in recommendations),
                "hardware_actions": action_count,
            },
        },
    })
