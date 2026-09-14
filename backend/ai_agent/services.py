"""Unified quality-gated LLM/VLM recommendation orchestration."""

import base64
import copy
import mimetypes
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from ai_agent.models import AIDecision
from ai_agent.parsing import parse_recommendation
from ai_agent.prompts import build_messages, build_vision_messages
from ai_agent.providers import get_provider, get_vlm_provider
from ai_agent.safety import run_safety_check
from cv.models import ImageAnalysis
from farm_state.services import build_farm_state
from telemetry.models import FarmDevice


class NoDeviceError(ValidationError):
    """Raised when a farm has no device to attach a decision to."""


class RecommendationGenerationError(RuntimeError):
    """Raised when neither configured model can generate a recommendation."""


def resolve_device(farm):
    device = FarmDevice.objects.filter(farm=farm).order_by("id").first()
    if device is None:
        raise NoDeviceError(
            f"Farm {farm.id} has no FarmDevice; a device is required to create an AIDecision."
        )
    return device


def latest_analysis_for_device(device):
    return (
        ImageAnalysis.objects.filter(image__camera__farm_level__device=device)
        .select_related("image", "image__camera")
        .order_by("-image__captured_at", "-id")
        .first()
    )


def _image_data_url(image):
    mime_type = mimetypes.guess_type(image.path.name)[0] or "image/jpeg"
    with image.path.open("rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def resolve_visual_context(device):
    analysis = latest_analysis_for_device(device)
    if analysis is None:
        return None, {
            "available": False,
            "status": "NO_ANALYSIS",
            "reason": "No analysed camera image is available for this device; sensor-only LLM used.",
            "quality_status": None,
            "quality_flags": [],
        }
    context = {
        "available": bool(analysis.vlm_ready),
        "status": "READY" if analysis.vlm_ready else "QUALITY_REJECTED",
        "reason": (
            "Image passed the CV quality gate and was supplied to the VLM."
            if analysis.vlm_ready
            else (analysis.quality_message or "Image failed the CV quality gate; sensor-only LLM used.")
        ),
        "quality_status": analysis.quality_status,
        "quality_flags": analysis.quality_flags,
        "image_id": analysis.image_id,
        "analysis_id": analysis.id,
        "camera_id": analysis.image.camera_id,
    }
    return analysis, context


def build_sensor_context(farm):
    """Return farm context with all CV-derived measurements removed."""
    farm_state = copy.deepcopy(build_farm_state(farm))
    for device in farm_state.get("devices", []):
        for level in device.get("levels", []):
            level["cameras"] = [
                {
                    key: camera[key]
                    for key in ("camera_id", "name", "status", "as_of", "age_seconds", "analysis_id", "image_id")
                    if key in camera
                }
                for camera in level.get("cameras", [])
            ]
    return farm_state


def _model_name(provider):
    return getattr(provider, "model_name", getattr(provider, "model", "unknown"))


def _complete_with_llm(farm_state, provider):
    system, user = build_messages(farm_state)
    return provider.complete(system, user)


def generate_recommendation(
    farm,
    device=None,
    provider=None,
    vlm_provider=None,
    persist=True,
):
    """Generate one notification using vision only when quality permits it."""
    device = device or resolve_device(farm)
    analysis, visual_context = resolve_visual_context(device)
    farm_state = build_sensor_context(farm)
    input_mode = "llm"
    fallback_used = False
    fallback_reason = ""
    selected_provider = None
    raw = None

    if visual_context["available"]:
        try:
            image_data_url = _image_data_url(analysis.image)
        except (FileNotFoundError, OSError, ValueError) as exc:
            visual_context.update({
                "available": False,
                "status": "IMAGE_UNREADABLE",
                "reason": f"Quality-approved image could not be read; sensor-only LLM used: {exc}",
            })
            fallback_used = True
            fallback_reason = visual_context["reason"]
        else:
            try:
                selected_provider = vlm_provider or get_vlm_provider()
                system, user = build_vision_messages(farm_state, visual_context)
                raw = selected_provider.complete(system, user, image_data_url=image_data_url)
                input_mode = "vlm"
            except Exception as exc:  # Provider adapters and injected test doubles.
                visual_context.update({
                    "available": False,
                    "status": "VLM_PROVIDER_ERROR",
                    "reason": f"Vision model failed; sensor-only LLM used: {exc}",
                })
                fallback_used = True
                fallback_reason = visual_context["reason"]

    if raw is None:
        try:
            selected_provider = provider or get_provider()
            raw = _complete_with_llm(farm_state, selected_provider)
        except Exception as exc:
            prefix = f"{fallback_reason} " if fallback_reason else ""
            raise RecommendationGenerationError(
                f"{prefix}Unable to generate a recommendation with the sensor-only LLM: {exc}"
            ) from exc

    parsed = parse_recommendation(raw)
    # Hardware execution is deliberately deferred. Preserve target/state as a
    # future-action suggestion, but never allow a model to mark it executable.
    parsed.execution_type = "notification"

    decision = None
    safety_check = None
    if persist:
        with transaction.atomic():
            decision = AIDecision.objects.create(
                device=device,
                input_mode=input_mode,
                model_name=_model_name(selected_provider),
                source_image=analysis.image if analysis else None,
                source_analysis=analysis,
                used_visual_input=input_mode == "vlm",
                visual_status=visual_context["status"],
                visual_reason=visual_context["reason"],
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                output_used_fallback=parsed.used_fallback,
                decision_type=parsed.decision_type,
                execution_type="notification",
                target_device=parsed.target_device,
                device_state=parsed.device_state,
                category=parsed.category,
                recommendation=parsed.recommendation,
                explanation=parsed.explanation,
                confidence_score=(Decimal(str(parsed.confidence)) if parsed.confidence is not None else None),
            )
            safety_check = run_safety_check(decision, farm_state, persist=True)

    notification_status = (
        "ready" if safety_check and safety_check["result"] == "passed" else "blocked"
    )
    return {
        "farm_id": farm.id,
        "device_id": device.id,
        "decision_id": decision.id if decision else None,
        "input_mode": input_mode,
        "model_name": _model_name(selected_provider),
        "source_image_id": analysis.image_id if analysis else None,
        "source_analysis_id": analysis.id if analysis else None,
        "used_visual_input": input_mode == "vlm",
        "visual_evidence": visual_context,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "notification_status": notification_status,
        "recommendation": parsed.as_dict(),
        "safety_check": safety_check,
        "used_output_fallback": parsed.used_fallback,
        "raw": raw,
    }
