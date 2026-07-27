from django.contrib import admin

from apps.accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "organization", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "organization")
