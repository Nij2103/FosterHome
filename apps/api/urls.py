"""
apps.api.urls

DRF DefaultRouter wires up every ViewSet with the standard REST
conventions (list/create at the collection URL, retrieve/update/delete
at the detail URL) plus the browsable API — visiting any of these URLs
in a regular browser while logged in renders an interactive HTML form,
which doubles as live API documentation (see also /api/v1/docs/ for a
plain-English endpoint reference).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.docs_views import api_docs
from apps.api.views.analytics_views import DashboardStatsView
from apps.api.views.children_views import ChildViewSet
from apps.api.views.families_views import FosterFamilyViewSet
from apps.api.views.placements_views import PlacementViewSet
from apps.api.views.predictions_views import PredictionViewSet
from apps.api.views.reports_views import ReportViewSet

app_name = "api"

router = DefaultRouter()
router.register(r"children", ChildViewSet, basename="child")
router.register(r"families", FosterFamilyViewSet, basename="family")
router.register(r"placements", PlacementViewSet, basename="placement")
router.register(r"predictions", PredictionViewSet, basename="prediction")
router.register(r"reports", ReportViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard-stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("docs/", api_docs, name="docs"),
]
