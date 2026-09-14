"""Manual harness to run the AI recommendation agent from the terminal.

Usage (from backend/):
    python manage.py ai_recommend <farm_id>

The AI agent auto-loads provider settings from the repo-root .env file.
If neither the shell nor .env sets AI_PROVIDER, it uses the "mock" provider
(no API key, no network). Shell variables still override .env values, e.g.:

    AI_PROVIDER=openrouter OPENROUTER_API_KEY=sk-or-... \\
        python manage.py ai_recommend 1

    AI_PROVIDER=ollama OLLAMA_MODEL=llama3.2 \\
        python manage.py ai_recommend 1
"""

import json

from django.core.management.base import BaseCommand, CommandError

from telemetry.models import Farm

from ai_agent.services import generate_recommendation, NoDeviceError


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
        except NoDeviceError as exc:
            raise CommandError(str(exc))

        self.stdout.write(json.dumps(result, indent=2))
