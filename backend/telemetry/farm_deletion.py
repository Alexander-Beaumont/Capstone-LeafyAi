import logging

from django.db import transaction
from django.shortcuts import get_object_or_404

from ai_agent.models import AIRecommendationRun
from telemetry.models import (
    ActuatorStateObservation,
    CameraImage,
    Farm,
    SensorReading,
    SetpointObservation,
)


logger = logging.getLogger(__name__)


def _delete_image_files(files):
    """Remove image files after their database rows have committed as deleted."""

    for storage, name in files:
        try:
            storage.delete(name)
        except Exception:
            # The database purge has already committed at this point. Reporting
            # the API deletion as failed would be misleading, so retain an
            # actionable log entry for deployment/storage remediation instead.
            logger.warning(
                "Farm was deleted, but camera image file %s could not be removed.",
                name,
                exc_info=True,
            )


@transaction.atomic
def purge_farm(farm_id):
    """Permanently delete a farm, its protected history, and captured media."""

    farm = get_object_or_404(Farm.objects.select_for_update(), pk=farm_id)

    images = list(
        CameraImage.objects.filter(
            camera__farm_level__device__farm=farm,
        ).only("path")
    )
    files = []
    seen_files = set()
    for image in images:
        if not image.path or not image.path.name:
            continue
        key = (id(image.path.storage), image.path.name)
        if key not in seen_files:
            seen_files.add(key)
            files.append((image.path.storage, image.path.name))

    # Recommendation runs link to readings and images through provenance M2M
    # tables. Remove the runs first so the historical evidence can be purged.
    AIRecommendationRun.objects.filter(farm=farm).delete()
    CameraImage.objects.filter(
        camera__farm_level__device__farm=farm,
    ).delete()
    SensorReading.objects.filter(sensor__device__farm=farm).delete()
    ActuatorStateObservation.objects.filter(device__farm=farm).delete()
    SetpointObservation.objects.filter(device__farm=farm).delete()

    farm.delete()
    transaction.on_commit(lambda: _delete_image_files(files))
