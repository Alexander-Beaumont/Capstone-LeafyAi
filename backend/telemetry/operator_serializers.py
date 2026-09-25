from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from rest_framework import serializers

from camera_capture.camera_collector import capture_decision
from camera_capture.config import SETTINGS as CAMERA_SETTINGS
from telemetry.models import Camera, CameraImage
from telemetry.serializers import CameraImageSerializer, CameraSerializer


class OperatorCameraImageSerializer(CameraImageSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    ai_used = serializers.SerializerMethodField()
    ai_run_ids = serializers.SerializerMethodField()

    class Meta(CameraImageSerializer.Meta):
        fields = CameraImageSerializer.Meta.fields + ["camera_name", "ai_used", "ai_run_ids"]

    def get_ai_used(self, obj):
        return obj.ai_recommendation_runs.exists()

    def get_ai_run_ids(self, obj):
        return list(obj.ai_recommendation_runs.order_by("id").values_list("id", flat=True))


class FarmCameraSerializer(CameraSerializer):
    latest_image = serializers.SerializerMethodField()
    last_capture_at = serializers.SerializerMethodField()
    next_scheduled_capture = serializers.SerializerMethodField()
    schedule_state = serializers.SerializerMethodField()
    image_quality = serializers.SerializerMethodField()

    class Meta(CameraSerializer.Meta):
        fields = CameraSerializer.Meta.fields + [
            "latest_image", "last_capture_at", "next_scheduled_capture",
            "schedule_state", "image_quality",
        ]
        read_only_fields = [
            "latest_image", "last_capture_at", "next_scheduled_capture",
            "schedule_state", "image_quality",
        ]

    def validate_farm_level_id(self, level):
        farm = self.context.get("farm")
        if farm is not None and level.device.farm_id != farm.id:
            raise serializers.ValidationError("The farm level does not belong to this farm.")
        return level

    def _latest(self, obj):
        cache = getattr(obj, "_operator_latest_image", None)
        if cache is None:
            cache = CameraImage.objects.filter(camera=obj).order_by("-captured_at", "-id").first()
            obj._operator_latest_image = cache
        return cache

    def get_latest_image(self, obj):
        image = self._latest(obj)
        return CameraImageSerializer(image, context=self.context).data if image else None

    def get_last_capture_at(self, obj):
        image = self._latest(obj)
        return image.captured_at if image else None

    def _decision(self, obj):
        if obj.is_archived:
            return None, "archived"
        if not obj.enabled:
            return None, "disabled"
        latest = self._latest(obj)
        latest_payload = (
            {"camera_id": obj.id, "captured_at": latest.captured_at.isoformat()}
            if latest else None
        )
        payload = CameraSerializer(obj).data
        now = datetime.now(ZoneInfo(CAMERA_SETTINGS.timezone_name))
        decision = capture_decision(
            payload,
            latest_payload,
            now_local=now,
            timezone_name=CAMERA_SETTINGS.timezone_name,
        )
        if decision.due:
            state = "due"
        elif decision.reason == "outside active hours":
            state = "outside_window"
        else:
            state = "scheduled"
        return decision, state

    def get_next_scheduled_capture(self, obj):
        decision, state = self._decision(obj)
        if state != "outside_window":
            return decision.due_at if decision else None
        now = datetime.now(ZoneInfo(CAMERA_SETTINGS.timezone_name))
        candidate = datetime.combine(now.date(), obj.active_start_time, tzinfo=now.tzinfo)
        if obj.active_start_time < obj.active_end_time and now.time() >= obj.active_end_time:
            candidate += timedelta(days=1)
        return candidate

    def get_schedule_state(self, obj):
        _, state = self._decision(obj)
        return state

    def get_image_quality(self, obj):
        image = self._latest(obj)
        if not image:
            return None
        return {
            "status": image.quality_status,
            "flags": image.quality_flags,
            "message": image.quality_message,
            "metrics": image.quality_metrics,
            "vlm_ready": image.vlm_ready,
        }
