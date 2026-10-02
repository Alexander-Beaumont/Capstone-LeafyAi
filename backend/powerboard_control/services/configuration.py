"""Database-backed Powerboard configuration helpers."""

from django.conf import settings

from powerboard_control.models import PowerboardConfiguration


def bootstrap_environment_configuration(farm):
    """Seed the initial farm's two Powerboard IPs once from environment values.

    This deliberately mirrors ``sensor_ingest`` bootstrap behaviour. Environment
    values are only defaults for the first row creation. Once the row exists, the
    database is authoritative so a farmer's UI edits survive backend/container
    restarts and later ``bootstrap_leafy`` runs.
    """

    return PowerboardConfiguration.objects.get_or_create(
        farm=farm,
        defaults={
            "powerboard_1_ip": str(settings.LEAFY_POWERBOARD_1_IP or "").strip() or None,
            "powerboard_2_ip": str(settings.LEAFY_POWERBOARD_2_IP or "").strip() or None,
        },
    )
