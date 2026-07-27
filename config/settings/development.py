"""
Development settings.

Run with: DJANGO_SETTINGS_MODULE=config.settings.development
(This is already the default set in manage.py for local work.)
"""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]  # fine for local development only

# SQLite per project requirement — file lives at the project root.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Show more detailed logs for OUR code while developing, without dragging
# every third-party library (e.g. pdfminer, used by pdfplumber) into
# DEBUG-level verbosity — that produces an unreadable wall of low-level
# parser output for a single command run.
LOGGING["loggers"] = {
    "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    "ml": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
}
