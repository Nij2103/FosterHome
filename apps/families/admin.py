from django.contrib import admin

from apps.families.models import FosterFamily


@admin.register(FosterFamily)
class FosterFamilyAdmin(admin.ModelAdmin):
    list_display = (
        "family_name", "state", "capacity", "current_occupancy",
        "available_slots", "home_type", "is_active",
    )
    list_filter = ("state", "home_type", "is_active", "accepts_special_needs")
    search_fields = ("family_name", "state")
