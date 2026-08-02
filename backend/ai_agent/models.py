from django.db import models
from backend.telemetry.models import PlantBatch

# AI Decision anc Check
class AIDecision(models.Model):
    plant_batch = models.ForeignKey(PlantBatch, on_delete=models.CASCADE)
    decision_type = models.CharField(max_length=100)
    recommendation = models.TextField()
    explanation = models.TextField()
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.recommendation


class SafetyCheck(models.Model):
    ai_decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE)
    checked_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=100)
    explanation = models.TextField()

    def __str__(self):
        return f"Safety Check for Action {self.ai_decision.id} - Result: {self.result}"

class HumanApproval(models.Model):
    ai_decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE)
    result = models.CharField(max_length=100)
    comment = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Action {self.ai_decision.id} - Approved: {self.result}"
    
class FarmAction(models.Model):
    ai_decision = models.ForeignKey(AIDecision, on_delete=models.CASCADE)
    result = models.CharField(max_length=100)
    explanation = models.TextField()
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Action {self.ai_decision.id} - Executed: {self.result}"
