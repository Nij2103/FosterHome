from django.urls import path

from apps.children import views

app_name = "children"

urlpatterns = [
    path("", views.ChildListView.as_view(), name="index"),
    path("add/", views.ChildCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ChildDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ChildUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ChildDeleteView.as_view(), name="delete"),
]
