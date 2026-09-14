from django.db import migrations, models


def archive_legacy_webcams(apps, schema_editor):
    Camera = apps.get_model("telemetry", "Camera")
    Camera.objects.filter(source_type="WEBCAM").update(
        enabled=False,
        cv_enabled=False,
        is_archived=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0010_camera_is_archived"),
    ]

    operations = [
        migrations.RunPython(archive_legacy_webcams, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="camera",
            name="source_type",
            field=models.CharField(choices=[("RTSP", "RTSP")], max_length=20),
        ),
        migrations.RemoveField(
            model_name="camera",
            name="webcam_index",
        ),
    ]
