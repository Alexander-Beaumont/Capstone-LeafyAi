from django.db import models

# Create your models here.
class AIDecision(models.Model):
    decision_type = models.CharField(max_length=100)
    recommendation = models.TextField()
    explanation = models.TextField()
    confidence_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.recommendation

class Action(models.Model):
    ai_decision = models.ForeignKey(AIDecision, on_delete=models.CASCADE)
    result = models.CharField(max_length=100)
    explanation = models.TextField()
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.result

class HumanApproval(models.Model):
    ai_decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE, primary_key=True)
    result = models.CharField(max_length=100)
    comments = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Action {self.action.id} - Approved: {self.result}"

class safetyCheck(models.Model):
    ai_decision = models.OneToOneField(AIDecision, on_delete=models.CASCADE, primary_key=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=100)
    explanation = models.TextField()

    def __str__(self):
        return f"Safety Check for Action {self.action.id} - Result: {self.result}"
