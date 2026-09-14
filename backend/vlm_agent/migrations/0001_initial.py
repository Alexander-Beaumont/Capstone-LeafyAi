from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cv", "0005_sync_whole_image_analysis"),
        ("telemetry", "0009_remove_cameraimage_timestamp_cameraimage_captured_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="VLMDecision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("used_visual_input", models.BooleanField(default=False)),
                ("visual_status", models.CharField(max_length=32)),
                ("visual_reason", models.TextField(blank=True)),
                ("model_name", models.CharField(max_length=255)),
                ("decision_type", models.CharField(max_length=50)),
                ("execution_type", models.CharField(choices=[("automated", "Automated"), ("notification", "Notification")], default="notification", max_length=20)),
                ("target_device", models.CharField(choices=[("fans", "Fans"), ("light", "Light"), ("none", "None")], default="none", max_length=20)),
                ("device_state", models.CharField(choices=[("on", "On"), ("off", "Off"), ("none", "None")], default="none", max_length=20)),
                ("category", models.CharField(choices=[("climate", "Climate"), ("lighting", "Lighting"), ("dosing", "Dosing"), ("water", "Water"), ("harvest", "Harvest"), ("alert", "Alert")], default="alert", max_length=20)),
                ("recommendation", models.TextField()),
                ("explanation", models.TextField()),
                ("confidence_score", models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="telemetry.farmdevice")),
                ("source_analysis", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="vlm_decisions", to="cv.imageanalysis")),
                ("source_image", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="vlm_decisions", to="telemetry.cameraimage")),
            ],
        ),
        migrations.CreateModel(
            name="VLMHumanApproval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("result", models.CharField(blank=True, choices=[("approved", "Approved"), ("denied", "Denied"), ("overridden", "Overridden")], max_length=20, null=True)),
                ("comment", models.TextField(blank=True, null=True)),
                ("decision", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="vlm_agent.vlmdecision")),
            ],
        ),
        migrations.CreateModel(
            name="VLMSafetyCheck",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checked_at", models.DateTimeField(auto_now_add=True)),
                ("result", models.CharField(choices=[("passed", "Passed"), ("failed", "Failed"), ("requires_review", "Requires Review")], max_length=20)),
                ("explanation", models.TextField(blank=True, null=True)),
                ("decision", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="vlm_agent.vlmdecision")),
            ],
        ),
        migrations.CreateModel(
            name="VLMFarmAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("executed_at", models.DateTimeField(blank=True, null=True)),
                ("result", models.CharField(blank=True, choices=[("success", "Success"), ("failed", "Failed"), ("partial", "Partial")], max_length=20, null=True)),
                ("explanation", models.TextField(blank=True, null=True)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="vlm_agent.vlmdecision")),
            ],
        ),
    ]
