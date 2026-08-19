"""
apps.api.views.families_views
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.api.permissions import IsAdminOrCaseWorkerForWrite
from apps.api.serializers.families_serializers import FosterFamilySerializer
from apps.families.models import FosterFamily


class FosterFamilyViewSet(viewsets.ModelViewSet):
    serializer_class = FosterFamilySerializer
    permission_classes = [IsAdminOrCaseWorkerForWrite]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["state", "home_type", "accepts_special_needs", "accepts_sibling_groups", "is_active"]
    search_fields = ["family_name", "state"]
    ordering_fields = ["capacity", "experience_years", "created_at"]

    def get_queryset(self):
        qs = FosterFamily.objects.all().order_by("-created_at")
        user = self.request.user
        if user and user.is_authenticated and not user.is_superuser:
            profile = getattr(user, "profile", None)
            if profile and profile.is_viewer:
                qs = qs.filter(created_by=user)
        return qs
