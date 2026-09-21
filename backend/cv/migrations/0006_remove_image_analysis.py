from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_agent", "0004_recommendation_runs_and_automation"),
        ("cv", "0005_sync_whole_image_analysis"),
    ]

    operations = [migrations.DeleteModel(name="ImageAnalysis")]
