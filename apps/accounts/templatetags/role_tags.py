"""
apps.accounts.templatetags.role_tags

Custom Django template filters for role-based UI element gating.

USAGE IN TEMPLATES:
    {% load role_tags %}
    {% if request.user|can_edit %}
        <a href="..." class="btn btn-primary">Edit Record</a>
    {% endif %}
"""

from django import template
from apps.accounts.models import Profile

register = template.Library()


@register.filter(name="can_edit")
def can_edit(user):
    """
    Returns True if user has Admin or Case Worker privileges (or is a Django superuser/staff).
    Returns False for Viewer or unauthenticated users.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    if not profile:
        return False
    return profile.role in (Profile.Role.ADMIN, Profile.Role.CASEWORKER)


@register.filter(name="is_viewer")
def is_viewer(user):
    """
    Returns True if user is a logged-in Viewer (i.e. cannot edit).
    """
    if not user or not user.is_authenticated:
        return False
    return not can_edit(user)
