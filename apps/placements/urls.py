from django.urls import path

from apps.placements import views

app_name = "placements"

urlpatterns = [
    path("", views.PlacementListView.as_view(), name="index"),
    path("export/csv/", views.export_placements_csv, name="export_csv"),

    path("add/", views.PlacementCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PlacementDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PlacementUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PlacementDeleteView.as_view(), name="delete"),
]
