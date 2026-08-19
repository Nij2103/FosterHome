"""
Root URL configuration.

WHY THIS STRUCTURE:
Each app owns its own urls.py (e.g. apps/children/urls.py) and is included
here with a namespace. This keeps routing decentralized — when we add a
new page inside the 'children' app later, we never touch this file, we
only touch apps/children/urls.py. That is what "modular" means in practice.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Core pages: landing, about, contact
    path("", include(("apps.core.urls", "core"), namespace="core")),

    # Auth: login, register, forgot password, profile, settings
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),

    # Domain apps
    path("children/", include(("apps.children.urls", "children"), namespace="children")),
    path("families/", include(("apps.families.urls", "families"), namespace="families")),
    path("placements/", include(("apps.placements.urls", "placements"), namespace="placements")),
    path("predictions/", include(("apps.predictions.urls", "predictions"), namespace="predictions")),

    # Dashboard & analytics
    path("analytics/", include(("apps.analytics.urls", "analytics"), namespace="analytics")),
    path("reports/", include(("apps.reports.urls", "reports"), namespace="reports")),

    # REST API (versioned under /api/v1/ so future breaking changes don't
    # disturb existing API consumers — a good practice to mention in docs)
    path("api/v1/", include(("apps.api.urls", "api"), namespace="api")),
    path("api-auth/", include("rest_framework.urls")),  # DRF's browsable-API login
]

# Serve user-uploaded media files (avatars, document uploads) during development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
