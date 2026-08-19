from django.urls import path

from apps.families import views

app_name = "families"

urlpatterns = [
    path("", views.FosterFamilyListView.as_view(), name="index"),
    path("add/", views.FosterFamilyCreateView.as_view(), name="create"),
    path("<int:pk>/", views.FosterFamilyDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.FosterFamilyUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.FosterFamilyDeleteView.as_view(), name="delete"),
]
