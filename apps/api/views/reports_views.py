"""
apps.api.views.reports_views
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.reports_serializers import ReportSerializer
from apps.reports.models import Report


class ReportViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only — Reports are only created by the scrape_reports management command (Step 6)."""
    queryset = Report.objects.prefetch_related("statistics").order_by("-scraped_at")
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["file_type", "published_year"]
    search_fields = ["title"]
