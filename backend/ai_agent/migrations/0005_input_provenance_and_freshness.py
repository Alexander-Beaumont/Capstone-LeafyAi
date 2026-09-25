import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_agent", "0004_recommendation_runs_and_automation"),
        ("telemetry", "0014_remove_obsolete_cv_camera_fields"),
    ]

    operations = [
        migrations.AddField(model_name="aiconfiguration", name="max_image_age_minutes", field=models.PositiveIntegerField(default=60, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10080)])),
        migrations.AddField(model_name="airecommendationrun", name="input_freshness_summary", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="airecommendationrun", name="skip_reason", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="airecommendationrun", name="source_readings", field=models.ManyToManyField(blank=True, related_name="ai_recommendation_runs", to="telemetry.sensorreading")),
        migrations.AlterField(model_name="airecommendationrun", name="status", field=models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed"), ("skipped", "Skipped")], default="pending", max_length=12)),
    ]
