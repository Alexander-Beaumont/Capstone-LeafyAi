from django.db import models

from cv.models import ImageAnalysis
from telemetry.models import CameraImage, FarmDevice

# AI Decision anc Check
class AIDecision(models.Model):
    EXECUTION_TYPE_CHOICES = [
        ('notification', 'Notification'),
    ]
    TARGET_DEVICE_CHOICES = [
        ('fans', 'Fans'),
        ('light', 'Light'),
        ('none', 'None'),
    ]
    DEVICE_STATE_CHOICES = [
        ('on', 'On'),
        ('off', 'Off'),
        ('none', 'None'),
    ]
    CATEGORY_CHOICES = [
        ('climate', 'Climate'),
        ('lighting', 'Lighting'),
        ('dosing', 'Dosing'),
        ('water', 'Water'),
        ('harvest', 'Harvest'),
        ('alert', 'Alert'),
    ]
    INPUT_MODE_CHOICES = [
        ('llm', 'Sensor-only LLM'),
        ('vlm', 'Vision and sensor VLM'),
    ]

    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    input_mode = models.CharField(
        max_length=10,
        choices=INPUT_MODE_CHOICES,
        default='llm',
    )
    model_name = models.CharField(max_length=255, default='unknown')
    source_image = models.ForeignKey(
        CameraImage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ai_decisions',
    )
    source_analysis = models.ForeignKey(
        ImageAnalysis,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ai_decisions',
    )
    used_visual_input = models.BooleanField(default=False)
    visual_status = models.CharField(max_length=32, default='NO_ANALYSIS')
    visual_reason = models.TextField(blank=True, default='')
    fallback_used = models.BooleanField(default=False)
    fallback_reason = models.TextField(blank=True, default='')
    output_used_fallback = models.BooleanField(default=False)
    decision_type = models.CharField(max_length=50) # May add choices. e.g. schedue_update, dosing_adjustment, lighting_adjustment, fan_adjustment, alert
    execution_type = models.CharField(
        max_length=20,
        choices=EXECUTION_TYPE_CHOICES,
        default='notification'
    )
    target_device = models.CharField(
        max_length=20,
        choices=TARGET_DEVICE_CHOICES,
        default='none'
    )
    device_state = models.CharField(
        max_length=20,
        choices=DEVICE_STATE_CHOICES,
        default='none'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='alert'
    )
    recommendation = models.TextField()
    explanation = models.TextField()
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

class SafetyCheck(models.Model): 
    decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE)
    
    checked_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(
        max_length=20,
        choices=[
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ]
    )
    explanation = models.TextField(
        blank=True,
        null=True
    )

class FarmAction(models.Model):
    decision = models.ForeignKey(AIDecision, on_delete=models.CASCADE)
    executed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    result = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial'),
        ],
        blank=True,
        null=True
    )
    explanation = models.TextField(
        blank=True,
        null=True
    )
