"""Quality-gated VLM recommendation orchestration."""

import base64
import copy
import mimetypes
from decimal import Decimal

from django.core.exceptions import ValidationError

from ai_agent.parsing import parse_recommendation
from cv.models import ImageAnalysis
from farm_state.services import build_farm_state
from telemetry.models import FarmDevice
from vlm_agent.models import VLMDecision
from vlm_agent.prompts import build_messages
from vlm_agent.providers import get_provider
from vlm_agent.safety import run_safety_check


class NoDeviceError(ValidationError):
    """Raised when no farm device can own the VLM decision."""


def resolve_device(farm):
    device = FarmDevice.objects.filter(farm=farm).first()
    if device is None:
        raise NoDeviceError(
            f"Farm {farm.id} has no FarmDevice; a device is required to create a VLMDecision."
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
    """Return a local Django media image as an OpenRouter-compatible data URL."""
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
            "reason": "No analysed camera image is available for this device.",
            "quality_status": None,
            "quality_flags": [],
        }

    visual_context = {
        "available": bool(analysis.vlm_ready),
        "status": "READY" if analysis.vlm_ready else "QUALITY_REJECTED",
        "reason": (
            "Image passed the CV quality gate and was supplied to the VLM."
            if analysis.vlm_ready
            else analysis.quality_message or "Image did not pass the CV quality gate."
        ),
        "quality_status": analysis.quality_status,
        "quality_flags": analysis.quality_flags,
        "image_id": analysis.image_id,
        "analysis_id": analysis.id,
        "camera_id": analysis.image.camera_id,
    }

    if not analysis.vlm_ready:
        return analysis, visual_context

    try:
        visual_context["image_data_url"] = _image_data_url(analysis.image)
    except (FileNotFoundError, OSError, ValueError) as exc:
        visual_context.update(
            {
                "available": False,
                "status": "IMAGE_UNREADABLE",
                "reason": f"Quality-approved image could not be read: {exc}",
            }
        )
    return analysis, visual_context


def build_sensor_context(farm):
    """Return farm state without CV-derived numeric visual measurements."""
    farm_state = copy.deepcopy(build_farm_state(farm))
    for device in farm_state.get("devices", []):
        for level in device.get("levels", []):
            cameras = []
            for camera in level.get("cameras", []):
                cameras.append(
                    {
                        key: camera[key]
                        for key in (
                            "camera_id",
                            "name",
                            "status",
                            "as_of",
                            "age_seconds",
                            "analysis_id",
                            "image_id",
                        )
                        if key in camera
                    }
                )
            level["cameras"] = cameras
    return farm_state


def generate_recommendation(farm, device=None, provider=None, persist=True):
    device = device or resolve_device(farm)
    provider = provider or get_provider()
    analysis, visual_context = resolve_visual_context(device)
    farm_state = build_sensor_context(farm)
    system, user_text = build_messages(farm_state, visual_context)
    raw = provider.complete(
        system,
        user_text,
        image_data_url=visual_context.get("image_data_url"),
    )
    parsed = parse_recommendation(raw)

    decision_id = None
    safety_check = None
    if persist:
        decision = VLMDecision.objects.create(
            device=device,
            source_image=analysis.image if analysis else None,
            source_analysis=analysis,
            used_visual_input=visual_context["available"],
            visual_status=visual_context["status"],
            visual_reason=visual_context["reason"],
            model_name=getattr(provider, "model_name", "unknown"),
            decision_type=parsed.decision_type,
            execution_type=parsed.execution_type,
            target_device=parsed.target_device,
            device_state=parsed.device_state,
            category=parsed.category,
            recommendation=parsed.recommendation,
            explanation=parsed.explanation,
            confidence_score=(
                Decimal(str(parsed.confidence)) if parsed.confidence is not None else None
            ),
        )
        decision_id = decision.id
        safety_check = run_safety_check(
            decision,
            farm_state,
            visual_context,
            persist=True,
        )

    return {
        "farm_id": farm.id,
        "device_id": device.id,
        "decision_id": decision_id,
        "source_image_id": analysis.image_id if analysis else None,
        "source_analysis_id": analysis.id if analysis else None,
        "used_visual_input": visual_context["available"],
        "visual_evidence": {
            key: value
            for key, value in visual_context.items()
            if key != "image_data_url"
        },
        "model_name": getattr(provider, "model_name", "unknown"),
        "recommendation": parsed.as_dict(),
        "safety_check": safety_check,
        "used_fallback": parsed.used_fallback,
        "raw": raw,
    }
