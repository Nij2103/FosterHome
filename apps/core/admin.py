"""
apps.core.admin

Registers ContactMessage model in the Django Admin panel so Administrators can
view, filter, search, and manage submitted messages.
"""

from django.contrib import admin
from apps.core.models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "organization", "subject", "is_read", "created_at")
    list_filter = ("is_read", "subject", "created_at")
    search_fields = ("first_name", "last_name", "email", "organization", "message")
    readonly_fields = ("created_at",)
    list_editable = ("is_read",)
    ordering = ("-created_at",)

    actions = ["mark_as_read", "mark_as_unread"]

    @admin.action(description="Mark selected messages as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected messages as unread")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
