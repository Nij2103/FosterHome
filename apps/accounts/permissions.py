"""
apps.accounts.permissions

Reusable, role-aware access control for both function-based and
class-based views. Every other app imports from here instead of
re-implementing role checks, which is exactly the payoff of keeping
'accounts' as its own app (Step 2 design principle).

Two flavours are provided:
- `role_required` — decorator, for simple function-based views
- `RoleRequiredMixin` — mixin, for class-based views (ListView, DetailView, etc.)

Both check `request.user.profile.role`, which is guaranteed to exist for
every logged-in user because of the post_save signal in signals.py.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Decorator for function-based views.

    Usage:
        @role_required("admin", "caseworker")
        def create_placement(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            profile = getattr(request.user, "profile", None)
            if profile is None or profile.role not in allowed_roles:
                messages.error(request, "You don't have permission to access that page.")
                raise PermissionDenied("Insufficient role for this action.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class RoleRequiredMixin:
    """
    Mixin for class-based views. Set `allowed_roles` on the view, e.g.:

        class PlacementCreateView(RoleRequiredMixin, CreateView):
            allowed_roles = ("admin", "caseworker")
            ...

    Combines with Django's LoginRequiredMixin implicitly — if the user
    isn't authenticated at all, they're redirected to login rather than
    shown a 403, which is friendlier UX than a hard permission error.
    """
    allowed_roles: tuple = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        profile = getattr(request.user, "profile", None)
        if profile is None or (self.allowed_roles and profile.role not in self.allowed_roles):
            messages.error(request, "You don't have permission to access that page.")
            raise PermissionDenied("Insufficient role for this action.")

        return super().dispatch(request, *args, **kwargs)


class ViewerReadOnlyMixin:
    """
    Convenience mixin for views that Viewers may see but never mutate.
    Blocks POST/PUT/PATCH/DELETE for the Viewer role while still allowing
    GET — useful on views shared across roles (e.g. a detail page).
    """
    UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        profile = getattr(request.user, "profile", None)
        if profile and profile.is_viewer and request.method in self.UNSAFE_METHODS:
            messages.error(request, "Viewers have read-only access.")
            raise PermissionDenied("Viewers cannot modify data.")
        return super().dispatch(request, *args, **kwargs)
