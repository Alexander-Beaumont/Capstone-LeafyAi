from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0007_sync_camera_model"),
        ("cv", "0004_remove_plantvisionmeasurement"),
    ]

    operations = [
        migrations.DeleteModel(name="CameraSlotPosition"),
        migrations.DeleteModel(name="Slot"),
    ]
