from django.contrib import admin

from apps.placements.models import Placement


@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    list_display = ("child", "family", "status", "placed_by", "start_date", "end_date")
    list_filter = ("status",)
    search_fields = ("child__first_name", "family__family_name")
    autocomplete_fields = ("child", "family")
