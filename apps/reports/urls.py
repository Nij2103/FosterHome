from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportListView.as_view(), name="index"),
    path("scrape/", views.trigger_scrape, name="trigger_scrape"),
    path("export/statistics/csv/", views.export_statistics_csv, name="export_statistics_csv"),
    path("<int:pk>/", views.ReportDetailView.as_view(), name="detail"),
]
