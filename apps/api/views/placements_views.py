"""
apps.api.views.placements_views
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.api.permissions import IsAdminOrCaseWorkerForWrite
from apps.api.serializers.placements_serializers import PlacementSerializer
from apps.placements.models import Placement


class PlacementViewSet(viewsets.ModelViewSet):
    queryset = Placement.objects.select_related("child", "family", "placed_by").order_by("-created_at")
    serializer_class = PlacementSerializer
    permission_classes = [IsAdminOrCaseWorkerForWrite]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "child", "family"]
    ordering_fields = ["created_at", "start_date"]

    def perform_create(self, serializer):
        serializer.save(placed_by=self.request.user)
