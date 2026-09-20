import os
import sys

from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agent'

    def ready(self):
        if os.environ.get("AI_WEB_SCHEDULER_ENABLED", "false").lower() not in {"1", "true", "yes", "on"}:
            return
        blocked_commands = {"test", "migrate", "makemigrations", "collectstatic", "shell", "check"}
        if len(sys.argv) > 1 and sys.argv[1] in blocked_commands:
            return
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return
        from ai_agent.scheduler import start_scheduler

        start_scheduler()
