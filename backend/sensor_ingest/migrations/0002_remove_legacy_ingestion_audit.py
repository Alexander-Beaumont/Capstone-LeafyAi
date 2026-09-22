from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sensor_ingest", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="IngestionRecord",
        ),
        migrations.DeleteModel(
            name="IngestionSourceState",
        ),
    ]
