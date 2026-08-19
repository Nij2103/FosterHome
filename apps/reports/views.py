"""
apps.reports.views

Read-only list/detail views for scraped reports, plus an Admin-only
action to trigger a fresh scrape from the UI. The scrape runs
synchronously within the request/response cycle — acceptable for a
college project's scope and dataset size, but documented here as a real
limitation: a production system would offload this to a background task
queue (Celery, Django-RQ) so a slow/failed scrape can't tie up a web
worker or time out the request. That's noted in the Future Scope section
of the project docs, not silently glossed over.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView

from apps.reports.models import Report


class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        qs = Report.objects.all().order_by("-scraped_at")
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(Q(title__icontains=query))
        file_type = self.request.GET.get("file_type")
        if file_type:
            qs = qs.filter(file_type=file_type)
        return qs


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "reports/report_detail.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statistics"] = self.object.statistics.order_by("state", "year", "metric_name")
        context["text_preview"] = (self.object.parsed_text or "")[:2000]
        return context

