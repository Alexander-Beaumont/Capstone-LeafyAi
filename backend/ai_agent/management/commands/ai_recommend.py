"""Manual harness to run the AI recommendation agent from the terminal.

Usage (from backend/):
    python manage.py ai_recommend <farm_id>

Provider/model/credential selection comes from the farm's AIConfiguration.
Use the authenticated settings API or Django admin before running this command.
"""

import json

from django.core.management.base import BaseCommand, CommandError

from telemetry.models import Farm

from ai_agent.services import generate_recommendation, NoDeviceError, RecommendationGenerationError


class Command(BaseCommand):
    help = "Generate a farm recommendation via the configured AI provider."

    def add_arguments(self, parser):
        parser.add_argument("farm_id", type=int)

    def handle(self, *args, **options):
        farm_id = options["farm_id"]
        farm = Farm.objects.filter(id=farm_id).first()
        if farm is None:
            raise CommandError(f"Farm {farm_id} not found.")

        try:
            result = generate_recommendation(farm)
        except (NoDeviceError, RecommendationGenerationError) as exc:
            raise CommandError(str(exc))

        self.stdout.write(json.dumps(result, indent=2))
