from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0009_remove_cameraimage_timestamp_cameraimage_captured_at"),
        ("cv", "0004_remove_plantvisionmeasurement"),
    ]

    operations = [
        migrations.RemoveField(model_name="imageanalysis", name="visible_plant_count"),
        migrations.AddField(model_name="imageanalysis", name="crowding_percentage", field=models.DecimalField(max_digits=5, decimal_places=2, null=True)),
        migrations.AddField(model_name="imageanalysis", name="green_percentage", field=models.DecimalField(max_digits=5, decimal_places=2, null=True)),
        migrations.AddField(model_name="imageanalysis", name="growth_change", field=models.DecimalField(max_digits=8, decimal_places=2, null=True)),
        migrations.AddField(model_name="imageanalysis", name="quality_flags", field=models.JSONField(default=list)),
        migrations.AddField(model_name="imageanalysis", name="quality_message", field=models.TextField(default="")),
        migrations.AddField(model_name="imageanalysis", name="quality_status", field=models.CharField(default="UNKNOWN", max_length=16)),
        migrations.AddField(model_name="imageanalysis", name="vlm_ready", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="imageanalysis", name="yellow_percentage", field=models.DecimalField(max_digits=5, decimal_places=2, null=True)),
        migrations.AlterField(model_name="imageanalysis", name="image", field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="analysis", to="telemetry.cameraimage")),
        migrations.AlterField(model_name="imageanalysis", name="total_canopy_coverage", field=models.DecimalField(max_digits=5, decimal_places=2, null=True)),
    ]
