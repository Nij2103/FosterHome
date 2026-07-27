from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts & Roles"

    def ready(self):
        # Import signal handlers so they get registered when Django starts.
        import apps.accounts.signals  # noqa: F401
