"""Django startup configuration for Leafy AI runtime services."""

from __future__ import annotations

import os
import sys

from django.apps import AppConfig


class LeafyRuntimeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "leafy_runtime"

    def ready(self):
        """
        Start background workers only for Django runserver.

        Django's development autoreloader starts a parent process and then
        the actual server process. RUN_MAIN=true identifies the serving
        process so duplicate sensor/camera workers are not created.

        With --noreload there is only one process, so that case is handled
        separately.
        """

        # Do nothing for commands such as:
        #   manage.py test
        #   manage.py migrate
        #   manage.py shell
        #   manage.py collect_sensors
        if len(sys.argv) < 2:
            return

        if sys.argv[1] != "runserver":
            return

        runtime_enabled = os.getenv(
            "LEAFY_RUNTIME_ENABLED",
            "true",
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        if not runtime_enabled:
            print(
                "Leafy AI background runtime disabled "
                "by LEAFY_RUNTIME_ENABLED."
            )
            return

        running_without_reloader = "--noreload" in sys.argv

        running_reloader_child = (
            os.environ.get("RUN_MAIN") == "true"
        )

        # Do not start workers in the autoreloader parent process.
        if not (
            running_without_reloader
            or running_reloader_child
        ):
            return

        from .runtime import start_background_runtime

        start_background_runtime()
