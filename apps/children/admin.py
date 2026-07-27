from django.contrib import admin

from apps.children.models import Child


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("first_name", "age", "gender", "state", "special_needs", "is_placed")
    list_filter = ("state", "gender", "special_needs", "is_placed")
    search_fields = ("first_name", "state")
