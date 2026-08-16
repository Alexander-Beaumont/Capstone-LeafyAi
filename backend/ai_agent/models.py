from django.db import models
from telemetry.models import FarmDevice

# AI Decision anc Check
class AIDecision(models.Model):
    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    decision_type = models.CharField(max_length=50) # May add choices. e.g. schedue_update, dosing_adjustment, lighting_adjustment, fan_adjustment, alert
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
            ('requires_review', 'Requires Review'),
        ]
    )
    explanation = models.TextField(
        blank=True,
        null=True
    )

class HumanApproval(models.Model):
    decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE)
    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    result = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Approved'),
            ('denied', 'Denied'),
            ('overridden', 'Overridden'),
        ],
        blank=True,
        null=True
    )
    comment = models.TextField(
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