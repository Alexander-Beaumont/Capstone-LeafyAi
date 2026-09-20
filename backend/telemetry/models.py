from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class ObservationQuality(models.TextChoices):
    """Quality assigned to externally sourced observations.

    ``UNVERIFIED`` is deliberately the default for ThingSpeak because the
    owner-provided feed currently exposes values but not the ESP32 validity
    flags.  Operational safety is evaluated elsewhere; this field only
    describes confidence in the observation itself.
    """

    VALID = "valid", "Valid"
    UNVERIFIED = "unverified", "Unverified"
    SUSPECT = "suspect", "Suspect"


def _slug_base(value, fallback):
    base = slugify(value or "") or fallback
    return base[:70].rstrip("-_") or fallback


class Farm(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)


class FarmDevice(models.Model):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    device_type = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = _slug_base(self.name, "device")
            candidate = base
            suffix = 2
            queryset = FarmDevice.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class FarmLevel(models.Model):
    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    level_number = models.IntegerField(
        choices=[(1, "Top"), (2, "Bottom")]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(level_number__in=[1, 2]),
                name="level_number_must_be_1_or_2",
            ),
            models.UniqueConstraint(
                fields=["device", "level_number"],
                name="unique_level_per_device",
            ),
        ]


class GrowingArea(models.Model):
    farm_level = models.ForeignKey(FarmLevel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slot_count = models.IntegerField()


class PlantBatch(models.Model):
    plant_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    growth_stage = models.CharField(
        max_length=50,
        choices=[
            ("seedling", "Seedling"),
            ("early_growth", "Early Growth"),
            ("mature", "Mature"),
        ],
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("active", "Active"),
            ("harvested", "Harvested"),
            ("failed", "Failed"),
        ],
    )


class BatchPlacement(models.Model):
    plant_batch = models.ForeignKey(PlantBatch, on_delete=models.CASCADE)
    growing_area = models.ForeignKey(GrowingArea, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)


class Camera(models.Model):
    farm_level = models.ForeignKey(FarmLevel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=100, blank=True, null=True)
    source_type = models.CharField(
        max_length=20,
        choices=[
            ("RTSP", "RTSP"),
            ("WEBCAM", "Webcam"),
        ],
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    rtsp_port = models.IntegerField(blank=True, null=True)
    rtsp_path = models.CharField(max_length=255, blank=True, null=True)
    webcam_index = models.IntegerField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    capture_interval_minutes = models.PositiveIntegerField(default=30)
    active_start_time = models.TimeField(blank=True, null=True)
    active_end_time = models.TimeField(blank=True, null=True)


class CameraImage(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.PROTECT)
    captured_at = models.DateTimeField()
    path = models.ImageField(upload_to="camera_images/")


class Sensor(models.Model):
    """A physical sensor known to Leafy AI.

    ``slug`` is the stable machine identifier used by integrations.  Database
    primary keys are deliberately not part of the external sensor contract.
    ``sensor_type`` remains the canonical type consumed by farm-state/safety
    (for example ``ph`` or ``ambient_temperature``).
    """

    device = models.ForeignKey(
        FarmDevice,
        on_delete=models.CASCADE,
        related_name="sensors",
    )
    slug = models.SlugField(max_length=80, blank=True)
    sensor_type = models.CharField(max_length=50)
    unit = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    expected_interval_seconds = models.PositiveIntegerField(null=True, blank=True)
    stale_after_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device", "slug"],
                name="unique_sensor_slug_per_device",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = _slug_base(self.sensor_type, "sensor")
            candidate = base
            suffix = 2
            queryset = Sensor.objects.filter(device=self.device)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)


class SensorReading(models.Model):
    """Immutable-style historical measurement from a physical sensor."""

    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.PROTECT,
        related_name="readings",
    )
    value = models.DecimalField(max_digits=12, decimal_places=4)

    # When the source says the physical measurement occurred.
    measured_at = models.DateTimeField(default=timezone.now, db_index=True)
    # When Leafy AI persisted the observation.
    received_at = models.DateTimeField(auto_now_add=True)

    source = models.CharField(max_length=50, default="manual")
    source_channel_id = models.CharField(max_length=100, blank=True, default="")
    source_entry_id = models.PositiveBigIntegerField(null=True, blank=True)
    quality_status = models.CharField(
        max_length=20,
        choices=ObservationQuality.choices,
        default=ObservationQuality.UNVERIFIED,
    )
    quality_notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(
                fields=["sensor", "measured_at"],
                name="sensor_measured_idx",
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "sensor",
                    "source",
                    "source_channel_id",
                    "source_entry_id",
                ],
                name="unique_external_sensor_reading",
            )
        ]


class ActuatorStateObservation(models.Model):
    """Externally observed actuator state, not a command.

    ThingSpeak field 7 currently reports irrigation-pump state.  Keeping this
    distinct from control commands lets Leafy AI compare requested state with
    observed state later without pretending that a relay state is a sensor.
    """

    class State(models.TextChoices):
        OFF = "off", "Off"
        ON = "on", "On"

    device = models.ForeignKey(
        FarmDevice,
        on_delete=models.PROTECT,
        related_name="actuator_state_observations",
    )
    actuator_slug = models.SlugField(max_length=80)
    state = models.CharField(max_length=10, choices=State.choices)
    measured_at = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, default="manual")
    source_channel_id = models.CharField(max_length=100, blank=True, default="")
    source_entry_id = models.PositiveBigIntegerField(null=True, blank=True)
    quality_status = models.CharField(
        max_length=20,
        choices=ObservationQuality.choices,
        default=ObservationQuality.UNVERIFIED,
    )
    quality_notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(
                fields=["device", "actuator_slug", "measured_at"],
                name="actuator_obs_time_idx",
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "device",
                    "actuator_slug",
                    "source",
                    "source_channel_id",
                    "source_entry_id",
                ],
                name="uniq_external_actuator_obs",
            )
        ]


class SetpointObservation(models.Model):
    """Externally observed control setpoint.

    This records what the owner infrastructure reported as a target.  It is an
    observation, not automatically Leafy AI's authoritative control policy.
    """

    device = models.ForeignKey(
        FarmDevice,
        on_delete=models.PROTECT,
        related_name="setpoint_observations",
    )
    setpoint_slug = models.SlugField(max_length=80)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=50)
    measured_at = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, default="manual")
    source_channel_id = models.CharField(max_length=100, blank=True, default="")
    source_entry_id = models.PositiveBigIntegerField(null=True, blank=True)
    quality_status = models.CharField(
        max_length=20,
        choices=ObservationQuality.choices,
        default=ObservationQuality.UNVERIFIED,
    )
    quality_notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(
                fields=["device", "setpoint_slug", "measured_at"],
                name="setpoint_obs_time_idx",
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "device",
                    "setpoint_slug",
                    "source",
                    "source_channel_id",
                    "source_entry_id",
                ],
                name="uniq_external_setpoint_obs",
            )
        ]


class NutrientTank(models.Model):
    device = models.OneToOneField(FarmDevice, on_delete=models.CASCADE)
    capacity_l = models.DecimalField(max_digits=6, decimal_places=1)
    current_level_l = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
    )
    last_refill_date = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)


class Doser(models.Model):
    device = models.ForeignKey(FarmDevice, on_delete=models.CASCADE)
    chemical_type = models.CharField(max_length=50)
    concentration = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    flow_rate_ml_per_min = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
    )
    updated_at = models.DateTimeField(auto_now=True)


class SafeRange(models.Model):
    sensor_type = models.CharField(max_length=50)
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    severity = models.CharField(
        max_length=20,
        choices=[
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
    )
