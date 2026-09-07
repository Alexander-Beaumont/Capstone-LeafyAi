from django.contrib import admin

from telemetry.models import (
    ActuatorStateObservation,
    FarmDevice,
    Sensor,
    SensorReading,
    SetpointObservation,
)


@admin.register(FarmDevice)
class FarmDeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "farm", "device_type")
    search_fields = ("name", "slug")


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "sensor_type",
        "device",
        "unit",
        "enabled",
        "expected_interval_seconds",
        "stale_after_seconds",
    )
    list_filter = ("enabled", "sensor_type")
    search_fields = ("slug", "sensor_type", "device__name")


class ReadOnlyObservationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(SensorReading)
class SensorReadingAdmin(ReadOnlyObservationAdmin):
    list_display = (
        "id",
        "sensor",
        "value",
        "measured_at",
        "source",
        "source_entry_id",
        "quality_status",
    )
    list_filter = ("source", "quality_status", "sensor__sensor_type")
    ordering = ("-measured_at", "-id")


@admin.register(ActuatorStateObservation)
class ActuatorStateObservationAdmin(ReadOnlyObservationAdmin):
    list_display = (
        "id",
        "device",
        "actuator_slug",
        "state",
        "measured_at",
        "source_entry_id",
    )
    ordering = ("-measured_at", "-id")


@admin.register(SetpointObservation)
class SetpointObservationAdmin(ReadOnlyObservationAdmin):
    list_display = (
        "id",
        "device",
        "setpoint_slug",
        "value",
        "unit",
        "measured_at",
        "source_entry_id",
    )
    ordering = ("-measured_at", "-id")
