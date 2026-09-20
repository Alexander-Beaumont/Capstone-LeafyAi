"""Raw-image VLM/LLM recommendation orchestration and persistence."""

import base64
import mimetypes
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ai_agent.actuators import execute_decision
from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun
from ai_agent.parsing import parse_recommendations
from ai_agent.prompts import build_messages, build_vision_messages
from ai_agent.providers import get_provider, get_vlm_provider
from ai_agent.safety import run_safety_check
from farm_state.services import build_farm_state
from telemetry.models import Camera, CameraImage, FarmDevice


class NoDeviceError(ValidationError):
    pass


class RecommendationGenerationError(RuntimeError):
    def __init__(self, message, run=None):
        super().__init__(message)
        self.run = run


def resolve_device(farm):
    device = FarmDevice.objects.filter(farm=farm).order_by("id").first()
    if device is None:
        raise NoDeviceError(f"Farm {farm.id} has no FarmDevice; a device is required.")
    return device


def build_sensor_context(farm):
    """Compatibility name: farm state now contains raw image metadata, never CV analysis."""
    return build_farm_state(farm)


def _image_data_url(image):
    mime_type = mimetypes.guess_type(image.path.name)[0] or "image/jpeg"
    with image.path.open("rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def latest_images_for_farm(farm, limit):
    images = []
    cameras = Camera.objects.filter(farm_level__device__farm=farm, enabled=True).order_by("id")
    for camera in cameras:
        image = CameraImage.objects.filter(camera=camera).order_by("-captured_at", "-id").first()
        if image:
            images.append(image)
    images.sort(key=lambda item: (item.captured_at, item.id), reverse=True)
    return images[:limit]


def _provider_name(provider):
    return getattr(provider, "provider_name", provider.__class__.__name__.lower())


def _model_name(provider):
    return getattr(provider, "model_name", getattr(provider, "model", "unknown"))


def _read_images(images):
    readable, failures = [], []
    for image in images:
        try:
            data_url = _image_data_url(image)
        except (FileNotFoundError, OSError, ValueError) as exc:
            failures.append(f"Camera {image.camera_id} image {image.id} was unreadable: {exc}")
            continue
        readable.append(
            {
                "image": image,
                "label": f"Camera {image.camera_id} ({image.camera.name}), captured {image.captured_at.isoformat()}",
                "data_url": data_url,
            }
        )
    return readable, failures


def _validate_device_ids(items, farm):
    valid_ids = set(FarmDevice.objects.filter(farm=farm).values_list("id", flat=True))
    invalid = sorted({item.device_id for item in items if item.device_id not in valid_ids})
    if invalid:
        raise ValueError(f"Model returned device IDs outside this farm: {invalid}")
    automated_targets = []
    for item in items:
        if item.target_device in {"fans", "light"}:
            key = (item.device_id, item.target_device)
            if key in automated_targets:
                raise ValueError(f"Model returned duplicate automated target {item.target_device} for device {item.device_id}.")
            automated_targets.append(key)


def _persist_items(run, farm_state, items, default_device):
    decisions = []
    with transaction.atomic():
        for item in items:
            device = FarmDevice.objects.filter(id=item.device_id, farm=run.farm).first() or default_device
            target = item.target_device if item.target_device in dict(AIDecision.TARGET_DEVICE_CHOICES) else "none"
            state = item.device_state if item.device_state in {"on", "off", "none"} else "none"
            execution_type = "automated" if target in {"fans", "light"} and state in {"on", "off"} else "notification"
            decision = AIDecision.objects.create(
                run=run,
                device=device,
                decision_type=item.decision_type,
                execution_type=execution_type,
                target_device=target,
                device_state=state,
                category=item.category,
                recommendation=item.recommendation,
                explanation=item.explanation,
                confidence_score=Decimal(str(item.confidence)) if item.confidence is not None else None,
                output_used_fallback=item.used_fallback,
            )
            safety = run_safety_check(decision, farm_state, persist=True)
            decisions.append((decision, safety))
    for decision, safety in decisions:
        if safety["result"] == "passed" and decision.execution_type == "automated":
            execute_decision(decision)
    return [decision for decision, _ in decisions]


def generate_recommendation(
    farm,
    device=None,
    provider=None,
    vlm_provider=None,
    persist=True,
    trigger="manual",
    scheduled_for=None,
    run=None,
):
    default_device = device or resolve_device(farm)
    configuration, _ = AIConfiguration.objects.get_or_create(farm=farm)
    farm_state = build_sensor_context(farm)
    run = run or AIRecommendationRun.objects.create(
        farm=farm,
        trigger=trigger,
        scheduled_for=scheduled_for,
        status="pending",
    )
    run.status = "running"
    run.started_at = timezone.now()
    run.save(update_fields=["status", "started_at"])

    images = latest_images_for_farm(farm, configuration.max_images)
    run.source_images.set(images)
    readable, image_failures = _read_images(images)
    raw = None
    observations = []
    items = None
    fallback_reasons = list(image_failures)
    selected_provider = None

    if readable:
        try:
            selected_provider = vlm_provider or get_vlm_provider(configuration)
            metadata = [
                {"camera_id": item["image"].camera_id, "image_id": item["image"].id, "captured_at": item["image"].captured_at.isoformat()}
                for item in readable
            ]
            system, user = build_vision_messages(farm_state, metadata)
            raw = selected_provider.complete(system, user, images=readable)
            observations, items = parse_recommendations(raw, default_device.id)
            _validate_device_ids(items, farm)
            run.input_mode = "vlm"
        except Exception as exc:
            fallback_reasons.append(f"VLM failed: {exc}")
            raw = None
            items = None
    else:
        fallback_reasons.append("No readable raw camera image was available.")

    if items is None:
        try:
            selected_provider = provider or get_provider(configuration)
            system, user = build_messages(farm_state)
            raw = selected_provider.complete(system, user)
            observations, items = parse_recommendations(raw, default_device.id)
            _validate_device_ids(items, farm)
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
        _persist_items(run, farm_state, items, default_device)
    run.status = "completed"
    run.completed_at = timezone.now()
    run.save()

    from ai_agent.serializers import AIRecommendationRunSerializer

    return AIRecommendationRunSerializer(run).data
