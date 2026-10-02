from django.db import models

from telemetry.models import Farm


class PowerboardConfiguration(models.Model):
    """Per-farm physical Kasa strip addresses.

    Logical outlet IDs stay defined centrally in ``powerboard_control.config.DEVICES``.
    This model only records which two physical strips belong to a farm.
    """

    farm = models.OneToOneField(
        Farm,
        on_delete=models.CASCADE,
        related_name="powerboard_configuration",
    )
    powerboard_1_ip = models.GenericIPAddressField(blank=True, null=True)
    powerboard_2_ip = models.GenericIPAddressField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Powerboard configuration for farm {self.farm_id}"
