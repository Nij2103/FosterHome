"""
apps.api.permissions

DRF permission classes that mirror apps.accounts.permissions' role logic
(Step 5) so the API and the web UI enforce IDENTICAL rules — a Viewer
who can't create a Child through the web form also can't POST one via
the API. Keeping this as its own small module (rather than reusing the
web mixins, which are dispatch()-based and don't fit DRF's
has_permission() contract) avoids duplicating the actual ROLE DEFINITIONS
while still fitting DRF's expected interface.
"""

from rest_framework import permissions

from apps.accounts.models import Profile


class IsAdminOrCaseWorkerOrReadOnly(permissions.BasePermission):
    """
    Read (GET/HEAD/OPTIONS): any authenticated user, any role.
    Write (POST/PUT/PATCH/DELETE): Admin or Case Worker only — a Viewer
    gets 403, matching the web UI's ViewerReadOnlyMixin behavior exactly.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role in (Profile.Role.ADMIN, Profile.Role.CASEWORKER)


class IsAdminOnly(permissions.BasePermission):
    """Used for destructive actions restricted to Admin only, e.g. deletes."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profile = getattr(request.user, "profile", None)
        return profile is not None and profile.role == Profile.Role.ADMIN


class IsAdminOrCaseWorkerForWrite(permissions.BasePermission):
    """
    Object-level variant: allows read for anyone authenticated, but
    additionally routes DELETE specifically to Admin only, while POST/
    PUT/PATCH remain open to Admin/Case Worker — used on ViewSets where
    delete needs to be stricter than create/update (matching the web
    views' DeleteView allowed_roles = (Admin,) vs Create/UpdateView
    allowed_roles = (Admin, Case Worker)).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return False
        if request.method == "DELETE":
            return profile.role == Profile.Role.ADMIN
        return profile.role in (Profile.Role.ADMIN, Profile.Role.CASEWORKER)
