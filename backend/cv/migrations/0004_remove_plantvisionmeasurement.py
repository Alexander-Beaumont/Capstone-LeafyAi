from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0007_sync_camera_model"),
        ("cv", "0003_alter_plantvisionmeasurement_slot_and_more"),
    ]

    operations = [
        migrations.DeleteModel(name="PlantVisionMeasurement"),
    ]
