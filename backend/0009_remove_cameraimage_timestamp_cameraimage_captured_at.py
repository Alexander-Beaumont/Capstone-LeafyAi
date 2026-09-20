from django.db import migrations, models


def copy_capture_times(apps, schema_editor):
    CameraImage = apps.get_model("telemetry", "CameraImage")
    for image in CameraImage.objects.all().only("id", "timestamp"):
        image.captured_at = image.timestamp
        image.save(update_fields=["captured_at"])


class Migration(migrations.Migration):
    dependencies = [("telemetry", "0008_remove_slots_and_slot_positions")]

    operations = [
        migrations.AddField(
            model_name="cameraimage",
            name="captured_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(copy_capture_times, migrations.RunPython.noop),
        migrations.AlterField(model_name="cameraimage", name="captured_at", field=models.DateTimeField()),
        migrations.RemoveField(model_name="cameraimage", name="timestamp"),
    ]
