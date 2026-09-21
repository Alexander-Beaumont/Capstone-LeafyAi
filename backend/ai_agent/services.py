"""Quality-gated raw-image VLM/LLM recommendation orchestration."""
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


def _visual_evidence(images, selected_ids, eligible_ids):
    evidence = []
    for image in images:
        if image.id in selected_ids:
            reason = "Selected for VLM input."
        elif image.id in eligible_ids:
            reason = "Image passed the technical gate but its file could not be read."
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


def generate_recommendation(farm, device=None, provider=None, vlm_provider=None, persist=True, trigger="manual", scheduled_for=None, run=None):
    default_device = device or resolve_device(farm)
    configuration, _ = AIConfiguration.objects.get_or_create(farm=farm)
    farm_state = build_sensor_context(farm)
    run = run or AIRecommendationRun.objects.create(farm=farm, trigger=trigger, scheduled_for=scheduled_for)
    run.status, run.started_at = "running", timezone.now()
    run.save(update_fields=["status", "started_at"])

    candidates = latest_image_candidates(farm)
    eligible = [image for image in candidates if image.vlm_ready and image.quality_status in {"PASS", "WARN"}][:configuration.max_images]
    readable, failures = _read_images(eligible)
    selected_ids = {item["image"].id for item in readable}
    eligible_ids = {image.id for image in eligible}
    run.source_images.set(selected_ids)
    run.visual_evidence = _visual_evidence(candidates, selected_ids, eligible_ids)
    fallback_reasons = list(failures)
    raw = None
    observations = []
    items = None
    selected_provider = None

    if readable:
        try:
            selected_provider = vlm_provider or get_vlm_provider(configuration)
            metadata = [{"camera_id": item["image"].camera_id, "image_id": item["image"].id, "captured_at": item["image"].captured_at.isoformat(), "quality_status": item["image"].quality_status} for item in readable]
            system, user = build_vision_messages(farm_state, metadata)
            raw = selected_provider.complete(system, user, images=readable)
            observations, items = parse_recommendations(raw, default_device.id)
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
            raw = selected_provider.complete(system, user)
            observations, items = parse_recommendations(raw, default_device.id)
            _validate_items(items, farm)
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
