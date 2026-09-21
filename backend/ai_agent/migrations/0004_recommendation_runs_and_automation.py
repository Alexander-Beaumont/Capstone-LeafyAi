import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def migrate_legacy_decisions(apps, schema_editor):
    Decision = apps.get_model("ai_agent", "AIDecision")
    Run = apps.get_model("ai_agent", "AIRecommendationRun")
    FarmDevice = apps.get_model("telemetry", "FarmDevice")
    farm_by_device = dict(FarmDevice.objects.values_list("id", "farm_id"))
    for decision in Decision.objects.all().iterator():
        run = Run.objects.create(
            farm_id=farm_by_device[decision.device_id],
            trigger="legacy",
            status="completed",
            input_mode=decision.input_mode,
            provider_name="legacy",
            model_name=decision.model_name,
            fallback_used=decision.fallback_used,
            fallback_reason=decision.fallback_reason,
            completed_at=decision.created_at,
        )
        if decision.source_image_id:
            run.source_images.add(decision.source_image_id)
        decision.run_id = run.id
        decision.save(update_fields=["run"])


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0013_cameraimage_quality_flags_and_more"),
        ("ai_agent", "0003_unify_recommendation_agents"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("llm_provider", models.CharField(choices=[("openrouter", "OpenRouter"), ("ollama", "Ollama"), ("mock", "Mock")], default="mock", max_length=20)),
                ("llm_model", models.CharField(default="mock-llm", max_length=255)),
                ("llm_api_key_encrypted", models.TextField(blank=True, default="")),
                ("vlm_provider", models.CharField(choices=[("openrouter", "OpenRouter"), ("ollama", "Ollama"), ("mock", "Mock")], default="mock", max_length=20)),
                ("vlm_model", models.CharField(default="mock-vlm", max_length=255)),
                ("vlm_api_key_encrypted", models.TextField(blank=True, default="")),
                ("schedule_enabled", models.BooleanField(default=False)),
                ("timezone", models.CharField(default="Australia/Melbourne", max_length=64)),
                ("interval_minutes", models.PositiveIntegerField(default=30, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1440)])),
                ("active_start_time", models.TimeField(default="08:00")),
                ("active_end_time", models.TimeField(default="20:00")),
                ("max_images", models.PositiveSmallIntegerField(default=4, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(8)])),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("farm", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="ai_configuration", to="telemetry.farm")),
            ],
        ),
        migrations.CreateModel(
            name="AIRecommendationRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trigger", models.CharField(choices=[("manual", "Manual"), ("scheduled", "Scheduled"), ("legacy", "Legacy")], default="manual", max_length=12)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=12)),
                ("scheduled_for", models.DateTimeField(blank=True, null=True)),
                ("input_mode", models.CharField(choices=[("llm", "Sensor-only LLM"), ("vlm", "Vision and sensor VLM")], default="llm", max_length=10)),
                ("provider_name", models.CharField(default="unknown", max_length=32)),
                ("model_name", models.CharField(default="unknown", max_length=255)),
                ("visual_evidence", models.JSONField(blank=True, default=list)),
                ("image_observations", models.JSONField(blank=True, default=list)),
                ("fallback_used", models.BooleanField(default=False)),
                ("fallback_reason", models.TextField(blank=True, default="")),
                ("error", models.TextField(blank=True, default="")),
                ("raw_output", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_recommendation_runs", to="telemetry.farm")),
                ("source_images", models.ManyToManyField(blank=True, related_name="ai_recommendation_runs", to="telemetry.cameraimage")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddField(model_name="aidecision", name="run", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="ai_agent.airecommendationrun")),
        migrations.AddField(model_name="farmaction", name="target_device", field=models.CharField(blank=True, default="", max_length=20)),
        migrations.AddField(model_name="farmaction", name="powerboard_device_ids", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="farmaction", name="requested_state", field=models.CharField(blank=True, default="", max_length=10)),
        migrations.AddField(model_name="farmaction", name="previous_state", field=models.CharField(blank=True, default="", max_length=10)),
        migrations.AddField(model_name="farmaction", name="confirmed_state", field=models.CharField(blank=True, default="", max_length=10)),
        migrations.AddField(model_name="farmaction", name="attempted_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="farmaction", name="hardware_response", field=models.JSONField(blank=True, default=dict)),
        migrations.RunPython(migrate_legacy_decisions, migrations.RunPython.noop),
        migrations.RemoveField(model_name="aidecision", name="fallback_reason"),
        migrations.RemoveField(model_name="aidecision", name="fallback_used"),
        migrations.RemoveField(model_name="aidecision", name="input_mode"),
        migrations.RemoveField(model_name="aidecision", name="model_name"),
        migrations.RemoveField(model_name="aidecision", name="source_analysis"),
        migrations.RemoveField(model_name="aidecision", name="source_image"),
        migrations.RemoveField(model_name="aidecision", name="used_visual_input"),
        migrations.RemoveField(model_name="aidecision", name="visual_reason"),
        migrations.RemoveField(model_name="aidecision", name="visual_status"),
        migrations.AlterField(model_name="aidecision", name="run", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="ai_agent.airecommendationrun")),
        migrations.AlterField(model_name="aidecision", name="execution_type", field=models.CharField(choices=[("notification", "Notification"), ("automated", "Automated")], default="notification", max_length=20)),
        migrations.AlterField(model_name="aidecision", name="target_device", field=models.CharField(choices=[("fans", "Fans"), ("light", "Light"), ("irrigation_pump", "Irrigation pump"), ("nutrient_doser", "Nutrient doser"), ("ph_doser", "pH doser"), ("none", "None")], default="none", max_length=20)),
        migrations.AlterField(model_name="farmaction", name="decision", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="actions", to="ai_agent.aidecision")),
        migrations.AddConstraint(model_name="airecommendationrun", constraint=models.UniqueConstraint(condition=models.Q(("trigger", "scheduled")), fields=("farm", "scheduled_for"), name="unique_ai_schedule_slot")),
    ]
