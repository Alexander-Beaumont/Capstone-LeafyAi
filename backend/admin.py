from django.contrib import admin

from sensor_ingest.models import IngestionRecord, IngestionSourceState


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(IngestionSourceState)
class IngestionSourceStateAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "key",
        "provider",
        "external_source_id",
        "last_http_success_at",
        "last_source_measured_at",
        "consecutive_failures",
    )
    ordering = ("key",)


@admin.register(IngestionRecord)
class IngestionRecordAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "source",
        "source_entry_id",
        "source_measured_at",
        "status",
        "sensor_reading_count",
        "invalid_fields",
    )
    list_filter = ("status", "source")
    ordering = ("-source_measured_at", "-source_entry_id")
