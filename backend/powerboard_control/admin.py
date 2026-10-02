from django.contrib import admin

from .models import PowerboardConfiguration


@admin.register(PowerboardConfiguration)
class PowerboardConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "farm",
        "powerboard_1_ip",
        "powerboard_2_ip",
        "updated_at",
    )
    search_fields = ("farm__name", "powerboard_1_ip", "powerboard_2_ip")
