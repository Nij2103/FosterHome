from django.urls import path

from apps.predictions import views

app_name = "predictions"

urlpatterns = [
    path("", views.PredictionListView.as_view(), name="index"),
    path("export/csv/", views.export_predictions_csv, name="export_csv"),
    path("new/", views.PredictionCreateView.as_view(), name="create"),
    path("matching/", views.suitable_matches_api, name="matching"),
    path("<int:pk>/", views.PredictionDetailView.as_view(), name="detail"),
    path("<int:pk>/export/pdf/", views.export_prediction_pdf, name="export_pdf"),

]
