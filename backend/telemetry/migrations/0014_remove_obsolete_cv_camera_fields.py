from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("telemetry", "0013_cameraimage_quality_flags_and_more")]

    operations = [
        migrations.RemoveField(model_name="camera", name="cv_enabled"),
        migrations.RemoveField(model_name="camera", name="growth_baseline_reset_at"),
        migrations.RemoveField(model_name="camera", name="roi_points"),
    ]
