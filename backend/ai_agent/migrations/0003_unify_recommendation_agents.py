from django.db import migrations, models
import django.db.models.deletion


def fail_legacy_reviews(apps, schema_editor):
    SafetyCheck = apps.get_model("ai_agent", "SafetyCheck")
    AIDecision = apps.get_model("ai_agent", "AIDecision")
    SafetyCheck.objects.filter(result="requires_review").update(result="failed")
    AIDecision.objects.exclude(execution_type="notification").update(execution_type="notification")


class Migration(migrations.Migration):
    dependencies = [
        ("ai_agent", "0002_aidecision_action_metadata"),
        ("cv", "0005_sync_whole_image_analysis"),
    ]

    operations = [
        migrations.AddField(
            model_name="aidecision",
            name="input_mode",
            field=models.CharField(choices=[("llm", "Sensor-only LLM"), ("vlm", "Vision and sensor VLM")], default="llm", max_length=10),
        ),
        migrations.AddField(model_name="aidecision", name="model_name", field=models.CharField(default="unknown", max_length=255)),
        migrations.AddField(
            model_name="aidecision",
            name="source_image",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ai_decisions", to="telemetry.cameraimage"),
        ),
        migrations.AddField(
            model_name="aidecision",
            name="source_analysis",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ai_decisions", to="cv.imageanalysis"),
        ),
        migrations.AddField(model_name="aidecision", name="used_visual_input", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="aidecision", name="visual_status", field=models.CharField(default="NO_ANALYSIS", max_length=32)),
        migrations.AddField(model_name="aidecision", name="visual_reason", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="aidecision", name="fallback_used", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="aidecision", name="fallback_reason", field=models.TextField(blank=True, default="")),
        migrations.AddField(model_name="aidecision", name="output_used_fallback", field=models.BooleanField(default=False)),
        migrations.DeleteModel(name="HumanApproval"),
        migrations.RunPython(fail_legacy_reviews, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="safetycheck",
            name="result",
            field=models.CharField(choices=[("passed", "Passed"), ("failed", "Failed")], max_length=20),
        ),
        migrations.AlterField(
            model_name="aidecision",
            name="execution_type",
            field=models.CharField(choices=[("notification", "Notification")], default="notification", max_length=20),
        ),
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS vlm_agent_vlmfarmaction",
                "DROP TABLE IF EXISTS vlm_agent_vlmhumanapproval",
                "DROP TABLE IF EXISTS vlm_agent_vlmsafetycheck",
                "DROP TABLE IF EXISTS vlm_agent_vlmdecision",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
