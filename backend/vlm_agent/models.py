from django.db import models

from cv.models import ImageAnalysis
from telemetry.models import CameraImage, FarmDevice


class VLMDecision(models.Model):
    EXECUTION_TYPE_CHOICES = [
        ("automated", "Automated"),
        ("notification", "Notification"),
    ]
    TARGET_DEVICE_CHOICES = [
        ("fans", "Fans"),
        ("light", "Light"),
        ("none", "None"),
    ]
    DEVICE_STATE_CHOICES = [
        ("on", "On"),
        ("off", "Off"),
        ("none", "None"),
    ]
    CATEGORY_CHOICES = [
        ("climate", "Climate"),
        ("lighting", "Lighting"),
        ("dosing", "Dosing"),
        ("water", "Water"),
        ("harvest", "Harvest"),
        ("alert", "Alert"),
    ]

    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    source_image = models.ForeignKey(
        CameraImage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vlm_decisions",
    )
    source_analysis = models.ForeignKey(
        ImageAnalysis,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vlm_decisions",
    )
    used_visual_input = models.BooleanField(default=False)
    visual_status = models.CharField(max_length=32)
    visual_reason = models.TextField(blank=True)
    model_name = models.CharField(max_length=255)
    decision_type = models.CharField(max_length=50)
    execution_type = models.CharField(
        max_length=20,
        choices=EXECUTION_TYPE_CHOICES,
        default="notification",
    )
    target_device = models.CharField(
        max_length=20,
        choices=TARGET_DEVICE_CHOICES,
        default="none",
    )
    device_state = models.CharField(
        max_length=20,
        choices=DEVICE_STATE_CHOICES,
        default="none",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="alert",
    )
    recommendation = models.TextField()
    explanation = models.TextField()
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)


class VLMSafetyCheck(models.Model):
    decision = models.OneToOneField(VLMDecision, on_delete=models.CASCADE)
    checked_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(
        max_length=20,
        choices=[
            ("passed", "Passed"),
            ("failed", "Failed"),
            ("requires_review", "Requires Review"),
        ],
    )
    explanation = models.TextField(blank=True, null=True)


class VLMHumanApproval(models.Model):
    decision = models.OneToOneField(VLMDecision, on_delete=models.CASCADE)
    result = models.CharField(
        max_length=20,
        choices=[
            ("approved", "Approved"),
            ("denied", "Denied"),
            ("overridden", "Overridden"),
        ],
        blank=True,
        null=True,
    )
    comment = models.TextField(blank=True, null=True)


class VLMFarmAction(models.Model):
    decision = models.ForeignKey(VLMDecision, on_delete=models.CASCADE)
    executed_at = models.DateTimeField(blank=True, null=True)
    result = models.CharField(
        max_length=20,
        choices=[
            ("success", "Success"),
            ("failed", "Failed"),
            ("partial", "Partial"),
        ],
        blank=True,
        null=True,
    )
    explanation = models.TextField(blank=True, null=True)
