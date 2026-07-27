from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]
