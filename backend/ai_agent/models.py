from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from telemetry.models import CameraImage, Farm, FarmDevice


class AIConfiguration(models.Model):
    PROVIDER_CHOICES = [("openrouter", "OpenRouter"), ("ollama", "Ollama"), ("mock", "Mock")]

    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, related_name="ai_configuration")
    llm_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="mock")
    llm_model = models.CharField(max_length=255, default="mock-llm")
    llm_api_key_encrypted = models.TextField(blank=True, default="")
    vlm_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="mock")
    vlm_model = models.CharField(max_length=255, default="mock-vlm")
    vlm_api_key_encrypted = models.TextField(blank=True, default="")
    schedule_enabled = models.BooleanField(default=False)
    timezone = models.CharField(max_length=64, default="Australia/Melbourne")
    interval_minutes = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1), MaxValueValidator(1440)])
    active_start_time = models.TimeField(default="08:00")
    active_end_time = models.TimeField(default="20:00")
    max_images = models.PositiveSmallIntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(8)])
    updated_at = models.DateTimeField(auto_now=True)


class AIRecommendationRun(models.Model):
    TRIGGER_CHOICES = [("manual", "Manual"), ("scheduled", "Scheduled"), ("legacy", "Legacy")]
    STATUS_CHOICES = [("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")]
    INPUT_MODE_CHOICES = [("llm", "Sensor-only LLM"), ("vlm", "Vision and sensor VLM")]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="ai_recommendation_runs")
    trigger = models.CharField(max_length=12, choices=TRIGGER_CHOICES, default="manual")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    scheduled_for = models.DateTimeField(null=True, blank=True)
    input_mode = models.CharField(max_length=10, choices=INPUT_MODE_CHOICES, default="llm")
    provider_name = models.CharField(max_length=32, default="unknown")
    model_name = models.CharField(max_length=255, default="unknown")
    source_images = models.ManyToManyField(CameraImage, blank=True, related_name="ai_recommendation_runs")
    visual_evidence = models.JSONField(default=list, blank=True)
    image_observations = models.JSONField(default=list, blank=True)
    fallback_used = models.BooleanField(default=False)
    fallback_reason = models.TextField(blank=True, default="")
    error = models.TextField(blank=True, default="")
    raw_output = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["farm", "scheduled_for"], condition=models.Q(trigger="scheduled"), name="unique_ai_schedule_slot")]


class AIDecision(models.Model):
    EXECUTION_TYPE_CHOICES = [("notification", "Notification"), ("automated", "Automated")]
    TARGET_DEVICE_CHOICES = [("fans", "Fans"), ("light", "Light"), ("irrigation_pump", "Irrigation pump"), ("nutrient_doser", "Nutrient doser"), ("ph_doser", "pH doser"), ("none", "None")]
    DEVICE_STATE_CHOICES = [("on", "On"), ("off", "Off"), ("none", "None")]
    CATEGORY_CHOICES = [("climate", "Climate"), ("lighting", "Lighting"), ("dosing", "Dosing"), ("water", "Water"), ("harvest", "Harvest"), ("alert", "Alert")]

    run = models.ForeignKey(AIRecommendationRun, on_delete=models.CASCADE, related_name="recommendations")
    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    decision_type = models.CharField(max_length=50)
    execution_type = models.CharField(max_length=20, choices=EXECUTION_TYPE_CHOICES, default="notification")
    target_device = models.CharField(max_length=20, choices=TARGET_DEVICE_CHOICES, default="none")
    device_state = models.CharField(max_length=20, choices=DEVICE_STATE_CHOICES, default="none")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="alert")
    recommendation = models.TextField()
    explanation = models.TextField()
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    output_used_fallback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class SafetyCheck(models.Model):
    decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE)
    checked_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=[("passed", "Passed"), ("failed", "Failed")])
    explanation = models.TextField(blank=True, null=True)


class FarmAction(models.Model):
    decision = models.ForeignKey(AIDecision, on_delete=models.CASCADE, related_name="actions")
    target_device = models.CharField(max_length=20, blank=True, default="")
    powerboard_device_ids = models.JSONField(default=list, blank=True)
    requested_state = models.CharField(max_length=10, blank=True, default="")
    previous_state = models.CharField(max_length=10, blank=True, default="")
    confirmed_state = models.CharField(max_length=10, blank=True, default="")
    attempted_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=[("success", "Success"), ("failed", "Failed"), ("partial", "Partial")], null=True, blank=True)
    explanation = models.TextField(blank=True, null=True)
    hardware_response = models.JSONField(default=dict, blank=True)
