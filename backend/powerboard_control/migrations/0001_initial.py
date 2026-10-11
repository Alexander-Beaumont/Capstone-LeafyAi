# Initial per-farm Powerboard configuration schema.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("telemetry", "0014_remove_obsolete_cv_camera_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="PowerboardConfiguration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("powerboard_1_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("powerboard_2_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "farm",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="powerboard_configuration",
                        to="telemetry.farm",
                    ),
                ),
            ],
        ),
    ]
