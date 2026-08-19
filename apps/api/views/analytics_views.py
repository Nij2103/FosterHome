"""
apps.api.views.analytics_views

A plain APIView (not a ViewSet — there's no single "resource" here, just
an aggregate stats endpoint) exposing the same numbers the web dashboard
shows (apps.analytics.views.dashboard), so any external client (e.g. a
mobile app, or a colleague's own dashboard) can pull the same figures.
"""

from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from apps.predictions.models import Prediction


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "total_children": Child.objects.count(),
            "placed_children": Child.objects.filter(is_placed=True).count(),
            "total_families": FosterFamily.objects.count(),
            "available_families": FosterFamily.objects.filter(
                is_active=True, current_occupancy__lt=F("capacity"),
            ).count(),
            "active_placements": Placement.objects.filter(status="active").count(),
            "disrupted_placements": Placement.objects.filter(status="disrupted").count(),
            "total_predictions": Prediction.objects.count(),
        })
