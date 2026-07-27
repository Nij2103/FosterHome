from django.contrib.auth import views as auth_views
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    # Django's built-in auth views handle login/logout/password-reset
    # securely (hashing, CSRF, session handling) — reimplementing these
    # ourselves would be a security risk for no benefit.
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings_view, name="settings"),
]
