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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.management import call_command
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from apps.accounts.models import Profile
from apps.accounts.permissions import role_required
from apps.core.exports import export_as_csv
from apps.reports.models import Report, ReportStatistic

REPORT_STATISTIC_EXPORT_COLUMNS = [
    ("Report", lambda s: s.report.title),
    ("State", lambda s: s.state),
    ("Year", lambda s: s.year),
    ("Metric", lambda s: s.metric_name),
    ("Value", lambda s: s.value),
]


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


@role_required("admin")
def trigger_scrape(request):
    if request.method != "POST":
        return redirect("reports:index")
    try:
        call_command("scrape_reports", local_dir="ml/scraping/fixtures")
        messages.success(request, "Scrape complete — fixture reports re-ingested. "
                                   "(Live scraping from this UI is limited to the "
                                   "bundled fixtures; run `python manage.py scrape_reports` "
                                   "from the command line for live sources.)")
    except Exception as exc:
        messages.error(request, f"Scrape failed: {exc}")
    return redirect("reports:index")


@login_required
def export_statistics_csv(request):
    """Exports all extracted ReportStatistic rows — the real scraped
    AFCARS data from Step 6 — as a CSV, ready for further analysis in
    Excel/Pandas outside the app."""
    qs = ReportStatistic.objects.select_related("report").order_by("state", "year", "metric_name")
    return export_as_csv(qs, REPORT_STATISTIC_EXPORT_COLUMNS, "report_statistics_export")
