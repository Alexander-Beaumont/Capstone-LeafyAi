from django.db import migrations, models


class Migration(migrations.Migration):
    """Add Camera technical-quality state without rewriting team migration history."""

    dependencies = [
        ("telemetry", "0012_remove_camera_webcam_index_camera_is_archived_and_more"),
    ]

    operations = [
        migrations.RemoveField(model_name="camera", name="cv_enabled"),
        migrations.RemoveField(model_name="camera", name="growth_baseline_reset_at"),
        migrations.RemoveField(model_name="camera", name="roi_points"),
        migrations.AddField(
            model_name="cameraimage",
            name="vlm_ready",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="cameraimage",
            name="quality_status",
            field=models.CharField(default="UNKNOWN", max_length=16),
        ),
        migrations.AddField(
            model_name="cameraimage",
            name="quality_flags",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="cameraimage",
            name="quality_message",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="cameraimage",
            name="quality_metrics",
            field=models.JSONField(default=dict),
        ),
    ]
