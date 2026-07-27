"""
apps.api.views.children_views
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.api.permissions import IsAdminOrCaseWorkerForWrite
from apps.api.serializers.children_serializers import ChildSerializer
from apps.children.models import Child


class ChildViewSet(viewsets.ModelViewSet):
    """
    /api/v1/children/           GET (list, paginated+searchable), POST (Admin/Case Worker)
    /api/v1/children/{id}/      GET, PUT, PATCH (Admin/Case Worker), DELETE (Admin only)
    """
    queryset = Child.objects.all().order_by("-created_at")
    serializer_class = ChildSerializer
    permission_classes = [IsAdminOrCaseWorkerForWrite]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["state", "gender", "special_needs", "is_placed"]
    search_fields = ["first_name", "state"]
    ordering_fields = ["age", "created_at", "time_in_care_months"]
