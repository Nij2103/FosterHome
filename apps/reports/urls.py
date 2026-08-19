from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportListView.as_view(), name="index"),
    path("<int:pk>/", views.ReportDetailView.as_view(), name="detail"),
]
