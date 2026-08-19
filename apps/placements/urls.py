from django.urls import path

from apps.placements import views

app_name = "placements"

urlpatterns = [
    path("", views.PlacementListView.as_view(), name="index"),
    path("add/", views.PlacementCreateView.as_view(), name="create"),
    path("summary-api/", views.placement_summary_api, name="summary_api"),
    path("<int:pk>/", views.PlacementDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PlacementUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PlacementDeleteView.as_view(), name="delete"),
]
