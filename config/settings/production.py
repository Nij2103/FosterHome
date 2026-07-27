"""
Production settings placeholder.

NOTE FOR THE REPORT'S "FUTURE SCOPE" CHAPTER:
This project targets local/college evaluation, so full production hardening
(HTTPS enforcement, a managed Postgres database, environment-based secrets
via a vault, WhiteNoise/S3 for static & media, Sentry error tracking) is out
of scope for the submission but sketched here to demonstrate awareness of
what changes between environments. Because we used Django's ORM instead of
raw SQL, swapping SQLite for Postgres later only requires changing DATABASES
below and reinstalling one driver package (psycopg) — no application code
changes.
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# Example of how this would point to Postgres in a real deployment:
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ["DB_NAME"],
#         "USER": os.environ["DB_USER"],
#         "PASSWORD": os.environ["DB_PASSWORD"],
#         "HOST": os.environ["DB_HOST"],
#         "PORT": os.environ.get("DB_PORT", "5432"),
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
