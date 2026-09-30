"""Quality-gated raw-image VLM/LLM recommendation orchestration."""
import base64
import mimetypes
import time
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ai_agent.actuators import execute_decision
from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun
from ai_agent.observation_names import attach_camera_names
from ai_agent.parsing import parse_recommendations
from ai_agent.prompts import build_messages, build_vision_messages
from ai_agent.providers import ProviderError, get_provider, get_vlm_provider
from ai_agent.safety import run_safety_check
from farm_state.services import build_farm_state
from farm_state.thresholds import FRESH_THRESHOLD_SECONDS
from telemetry.models import Camera, CameraImage, FarmDevice, ObservationQuality, Sensor, SensorReading


class NoDeviceError(ValidationError):
    pass


class RecommendationGenerationError(RuntimeError):
    def __init__(self, message, run=None):
        super().__init__(message)
        self.run = run


LLM_RETRY_DELAYS_SECONDS = (1, 2, 4)


def resolve_device(farm):
    device = FarmDevice.objects.filter(farm=farm).order_by("id").first()
    if device is None:
        raise NoDeviceError(f"Farm {farm.id} has no FarmDevice; a device is required.")
    return device


def build_sensor_context(farm):
    return build_farm_state(farm)


def _image_data_url(image):
    mime_type = mimetypes.guess_type(image.path.name)[0] or "image/jpeg"
    with image.path.open("rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def latest_image_candidates(farm):
    images = []
    cameras = Camera.objects.filter(
        farm_level__device__farm=farm, enabled=True, is_archived=False
    ).order_by("id")
    for camera in cameras:
        image = CameraImage.objects.filter(camera=camera).order_by("-captured_at", "-id").first()
        if image:
            images.append(image)
    return sorted(images, key=lambda item: (item.captured_at, item.id), reverse=True)


def _visual_evidence(images, selected_ids, eligible_ids, *, cutoff=None):
    evidence = []
    for image in images:
        if image.id in selected_ids:
            reason = "Selected for VLM input."
        elif image.id in eligible_ids:
            reason = "Image passed the technical gate but its file could not be read."
        elif cutoff is not None and image.captured_at < cutoff:
            reason = "Image passed the technical gate but is older than the configured maximum age."
        elif image.vlm_ready and image.quality_status in {"PASS", "WARN"}:
            reason = "Image passed the technical gate but exceeded the configured image limit."
        else:
            reason = image.quality_message or "Image did not pass the technical VLM gate."
        evidence.append({
            "image_id": image.id,
            "camera_id": image.camera_id,
            "camera_name": image.camera.name,
            "captured_at": image.captured_at.isoformat(),
            "quality_status": image.quality_status,
            "quality_flags": image.quality_flags,
            "quality_message": image.quality_message,
            "vlm_ready": image.vlm_ready,
            "selected": image.id in selected_ids,
            "reason": reason,
        })
    return evidence


def _read_images(images):
    readable, failures = [], []
    for image in images:
        try:
            data_url = _image_data_url(image)
        except (FileNotFoundError, OSError, ValueError) as exc:
            failures.append(f"Camera {image.camera_id} image {image.id} was unreadable: {exc}")
            continue
        readable.append({
            "image": image,
            "label": f"Camera {image.camera_id} ({image.camera.name}), captured {image.captured_at.isoformat()}",
            "data_url": data_url,
        })
    return readable, failures


def _provider_name(provider):
    return getattr(provider, "provider_name", provider.__class__.__name__.lower())


def _model_name(provider):
    return getattr(provider, "model_name", getattr(provider, "model", "unknown"))


def _validate_items(items, farm):
    valid_ids = set(FarmDevice.objects.filter(farm=farm).values_list("id", flat=True))
    invalid = sorted({item.device_id for item in items if item.device_id not in valid_ids})
    if invalid:
        raise ValueError(f"Model returned device IDs outside this farm: {invalid}")
    seen = set()
    for item in items:
        if item.target_device in {"fans", "light"}:
            key = item.target_device
            if key in seen:
                raise ValueError(f"Model returned duplicate automated target {item.target_device}.")
            seen.add(key)


def _complete_llm_recommendations(provider, system, user, default_device_id, farm):
    """Return the first valid text-LLM response after silent bounded retries."""
    for attempt in range(len(LLM_RETRY_DELAYS_SECONDS) + 1):
        try:
            raw = provider.complete(system, user)
            observations, items = parse_recommendations(raw, default_device_id)
            _validate_items(items, farm)
            return raw, observations, items
        except ProviderError as exc:
            if not exc.retryable or attempt == len(LLM_RETRY_DELAYS_SECONDS):
                raise
        except ValueError:
            if attempt == len(LLM_RETRY_DELAYS_SECONDS):
                raise

        time.sleep(LLM_RETRY_DELAYS_SECONDS[attempt])


def _persist_items(run, farm_state, items):
    checked = []
    with transaction.atomic():
        for item in items:
            decision = AIDecision.objects.create(
                run=run,
                device_id=item.device_id,
                decision_type=item.decision_type,
                execution_type=item.execution_type,
                target_device=item.target_device,
                device_state=item.device_state,
                category=item.category,
                recommendation=item.recommendation,
                explanation=item.explanation,
                confidence_score=Decimal(str(item.confidence)) if item.confidence is not None else None,
            )
            checked.append((decision, run_safety_check(decision, farm_state, persist=True)))
    for decision, safety in checked:
        if safety["result"] == "passed" and decision.execution_type == "automated":
            execute_decision(decision)


def latest_fresh_readings(farm, now=None):
    """Return one fresh, non-suspect reading per enabled farm sensor."""
    now = now or timezone.now()
    readings = []
    summary = {"fresh": 0, "stale": 0, "missing": 0, "suspect": 0}
    sensors = Sensor.objects.filter(device__farm=farm, enabled=True).order_by("id")
    for sensor in sensors:
        reading = SensorReading.objects.filter(sensor=sensor).order_by(
            "-measured_at", "-id"
        ).first()
        if reading is None:
            summary["missing"] += 1
            continue
        if reading.quality_status == ObservationQuality.SUSPECT:
            summary["suspect"] += 1
            continue
        stale_after = sensor.stale_after_seconds or FRESH_THRESHOLD_SECONDS
        if reading.measured_at < now - timedelta(seconds=stale_after):
            summary["stale"] += 1
            continue
        summary["fresh"] += 1
        readings.append(reading)
    return readings, summary


def _restrict_farm_state_readings(farm_state, reading_ids):
    """Remove stale/suspect sensor values from scheduled model input."""
    reading_ids = set(reading_ids)
    for device in farm_state.get("devices", []):
        device["sensors"] = [
            sensor for sensor in device.get("sensors", [])
            if sensor.get("sensor_reading_id") in reading_ids
        ]
    return farm_state


def _input_reuse(farm, run, reading_ids, image_ids):
    completed = AIRecommendationRun.objects.filter(
        farm=farm, status="completed"
    ).exclude(id=run.id)
    previous = completed.order_by("-completed_at", "-id").first()
    previous_readings = set(SensorReading.objects.filter(
        ai_recommendation_runs__in=completed
    ).values_list("id", flat=True))
    previous_images = set(CameraImage.objects.filter(
        ai_recommendation_runs__in=completed
    ).values_list("id", flat=True))
    reading_ids = set(reading_ids)
    image_ids = set(image_ids)
    return previous, {
        "new_reading_ids": sorted(reading_ids - previous_readings),
        "reused_reading_ids": sorted(reading_ids & previous_readings),
        "new_image_ids": sorted(image_ids - previous_images),
        "reused_image_ids": sorted(image_ids & previous_images),
    }


def generate_recommendation(farm, device=None, provider=None, vlm_provider=None, persist=True, trigger="manual", scheduled_for=None, run=None):
    default_device = device or resolve_device(farm)
    configuration, _ = AIConfiguration.objects.get_or_create(farm=farm)
    now = timezone.now()
    farm_state = build_sensor_context(farm)
    run = run or AIRecommendationRun.objects.create(farm=farm, trigger=trigger, scheduled_for=scheduled_for)
    fresh_readings, sensor_summary = latest_fresh_readings(farm, now)
    reading_ids = {reading.id for reading in fresh_readings}
    run.source_readings.set(reading_ids)
    farm_state = _restrict_farm_state_readings(farm_state, reading_ids)
    candidates = latest_image_candidates(farm)
    image_cutoff = now - timedelta(minutes=configuration.max_image_age_minutes)
    eligible = [
        image for image in candidates
        if image.vlm_ready
        and image.quality_status in {"PASS", "WARN"}
        and image.captured_at >= image_cutoff
    ][:configuration.max_images]
    readable, failures = _read_images(eligible)
    selected_ids = {item["image"].id for item in readable}
    eligible_ids = {image.id for image in eligible}
    run.source_images.set(selected_ids)
    run.visual_evidence = _visual_evidence(
        candidates, selected_ids, eligible_ids, cutoff=image_cutoff
    )
    previous, reuse = _input_reuse(farm, run, reading_ids, selected_ids)
    run.input_freshness_summary = {
        "evaluated_at": now.isoformat(),
        "max_image_age_minutes": configuration.max_image_age_minutes,
        "sensors": {**sensor_summary, "included": len(reading_ids)},
        "images": {
            "latest_candidates": len(candidates),
            "technically_eligible": len(eligible_ids),
            "included": len(selected_ids),
        },
        "previous_completed_run_id": previous.id if previous else None,
        **reuse,
    }
    has_new_evidence = bool(reuse["new_reading_ids"] or reuse["new_image_ids"])
    if trigger == "scheduled" and previous is not None and not has_new_evidence:
        run.status = "skipped"
        run.skip_reason = "No new eligible sensor readings or camera images were available."
        run.started_at = now
        run.completed_at = timezone.now()
        run.save()
        from ai_agent.serializers import AIRecommendationRunSerializer
        return AIRecommendationRunSerializer(run).data

    run.status, run.started_at = "running", now
    run.save()
    fallback_reasons = list(failures)
    raw = None
    observations = []
    items = None
    selected_provider = None

    if readable:
        try:
            selected_provider = vlm_provider or get_vlm_provider(configuration)
            metadata = [{"camera_id": item["image"].camera_id, "camera_name": item["image"].camera.name, "image_id": item["image"].id, "captured_at": item["image"].captured_at.isoformat(), "quality_status": item["image"].quality_status} for item in readable]
            system, user = build_vision_messages(farm_state, metadata)
            raw = selected_provider.complete(system, user, images=readable)
            observations, items = parse_recommendations(raw, default_device.id)
            observations = attach_camera_names(
                observations,
                {
                    item["image"].camera_id: item["image"].camera.name
                    for item in readable
                },
            )
            _validate_items(items, farm)
            run.input_mode = "vlm"
        except Exception as exc:
            fallback_reasons.append(f"VLM failed: {exc}")
            raw, items = None, None
    else:
        fallback_reasons.append("No reliable readable camera image was available.")

    if items is None:
        try:
            selected_provider = provider or get_provider(configuration)
            system, user = build_messages(farm_state)
            raw, observations, items = _complete_llm_recommendations(
                selected_provider,
                system,
                user,
                default_device.id,
                farm,
            )
            run.input_mode = "llm"
        except Exception as exc:
            run.status = "failed"
            run.error = f"Unable to generate recommendations: {exc}"
            run.fallback_used = bool(fallback_reasons)
            run.fallback_reason = " ".join(fallback_reasons)
            run.completed_at = timezone.now()
            run.save()
            raise RecommendationGenerationError(run.error, run=run) from exc

    run.provider_name = _provider_name(selected_provider)
    run.model_name = _model_name(selected_provider)
    run.fallback_used = bool(fallback_reasons)
    run.fallback_reason = " ".join(fallback_reasons)
    run.image_observations = observations if run.input_mode == "vlm" else []
    run.raw_output = raw or ""
    if persist:
        _persist_items(run, farm_state, items)
    run.status, run.completed_at = "completed", timezone.now()
    run.save()

    from ai_agent.serializers import AIRecommendationRunSerializer
    return AIRecommendationRunSerializer(run).data
