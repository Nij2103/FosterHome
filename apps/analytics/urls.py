from django.urls import path

from apps.analytics import views

app_name = "analytics"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/export/pdf/", views.export_dashboard_pdf, name="export_dashboard_pdf"),
    path("visualizations/", views.visualizations, name="visualizations"),
    path("model-comparison/", views.model_comparison, name="model_comparison"),
]
