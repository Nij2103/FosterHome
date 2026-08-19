"""
Base settings shared by every environment (development, production).

WHY THIS FILE EXISTS:
Splitting settings into base/development/production is a standard Django
pattern for final-year and production projects alike. It lets us keep
environment-specific values (DEBUG, ALLOWED_HOSTS, database path) isolated
from the settings that never change, and makes it obvious in a viva that
we understand dev vs prod hygiene.
"""

import os
from pathlib import Path

# BASE_DIR points to the project root (foster_care_predictor/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECRET_KEY is read from an environment variable so it is never committed
# to source control. .env.example documents the variable name for graders.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-THIS-IN-PRODUCTION-see-env-example",
)

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # nice number/date formatting in templates
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
]

# Every custom app lives inside apps/ and is referenced by its dotted path,
# e.g. "apps.children", so Django's AppConfig can find it.
LOCAL_APPS = [
    "apps.accounts",
    "apps.children",
    "apps.families",
    "apps.placements",
    "apps.predictions",
    "apps.analytics",
    "apps.reports",
    "apps.core",
    "apps.api",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Global templates (base.html, navbar, footer) live at the project
        # root templates/ folder. Django also auto-discovers each app's own
        # templates/<app_name>/ folder because APP_DIRS is True below.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Password validation (Django's built-in strength rules)
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # populated by collectstatic in production

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Auth redirects
# ---------------------------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "analytics:dashboard"
LOGOUT_REDIRECT_URL = "core:landing"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ---------------------------------------------------------------------------
# Path to the ml/ package's saved model artifacts, so Django views can load
# trained models without hardcoding paths in multiple places.
# ---------------------------------------------------------------------------
ML_MODELS_DIR = BASE_DIR / "ml" / "models_store"
ML_DATA_PROCESSED_DIR = BASE_DIR / "ml" / "data" / "processed"

# ---------------------------------------------------------------------------
# Logging (basic, console-based — sufficient for a college project, easy to
# extend to file/rotating handlers for the "production" settings later).
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
