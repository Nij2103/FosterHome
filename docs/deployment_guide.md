# Deployment Guide

This project targets local/college evaluation by design (see the main
README and `config/settings/production.py`'s docstring), so this guide
describes what would need to change for a real deployment — partly
implemented already, partly sketched — rather than a guide for a
deployment that's already fully built out.

## What's already in place for production

- **Settings split** (`config/settings/base.py` / `development.py` /
  `production.py`) — switching environments is `DJANGO_SETTINGS_MODULE`,
  no code changes.
- **`production.py` already sets** `DEBUG = False`,
  `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
  and `SECURE_HSTS_SECONDS` — the standard Django security checklist
  items (`python manage.py check --deploy` verifies these).
- **`SECRET_KEY` is read from an environment variable**, never
  hardcoded, with a clearly-marked insecure fallback for local dev only.
- **The database swap is a two-line change** (per `production.py`'s
  commented-out Postgres block) precisely because every query in this
  project goes through Django's ORM — no raw SQL to audit for
  database-specific syntax.

## What would need to change for a real deployment

1. **Switch `DATABASES` to Postgres** (or MySQL) — SQLite is fine for
   this project's evaluation scope but isn't suited to concurrent
   production writes. `pip install psycopg[binary]` and uncomment the
   Postgres block in `production.py`.
2. **Static/media files** — `STATIC_ROOT`/`MEDIA_ROOT` currently point
   at local disk. In production, run `python manage.py collectstatic`
   and serve static files via a CDN or WhiteNoise, and move
   `media/analytics/charts/` (and scraped report PDFs) to object storage
   (S3-compatible) rather than local disk, which doesn't survive
   container restarts on most hosting platforms.
3. **Background jobs for the scraper and ML training** — both
   `scrape_reports` and `train_models` currently run synchronously
   (`call_command()` inside a request, or directly via the CLI). This is
   fine for a scheduled/manual admin action at this project's scale, but
   a production system should move both to a task queue (Celery +
   Redis, or Django-RQ) so a slow scrape or a multi-minute training run
   never ties up a web worker or risks a request timeout. This is
   flagged explicitly in `apps/reports/views.py`'s `trigger_scrape` view
   docstring, not silently glossed over.
4. **WSGI/ASGI server** — the Django dev server
   (`manage.py runserver`) is explicitly not for production (Django
   prints this warning itself). Use Gunicorn or uWSGI behind Nginx, or
   an ASGI server (Uvicorn/Daphne) if you build out the async features
   `config/asgi.py` is already scaffolded for.
5. **`ALLOWED_HOSTS`** — set via the `DJANGO_ALLOWED_HOSTS` environment
   variable to your real domain(s); the current placeholder is empty.
6. **Model artifact deployment** — `ml/models_store/` currently ships
   inside the same codebase/container as the web app. At larger scale,
   trained model artifacts would typically be versioned and deployed
   separately (e.g. pulled from object storage at container start) so
   retraining doesn't require a full app redeploy.
7. **Environment secrets** — move from a local `.env` file to your
   platform's secret manager (AWS Secrets Manager, Railway/Render env
   vars, etc.) rather than shipping `.env` in any deployment artifact.
8. **Logging/monitoring** — the current `LOGGING` config
   (`config/settings/base.py`) is console-only, appropriate for local
   dev. Production would add structured logging + an error tracker
   (e.g. Sentry) so failures are visible without SSHing into a server.

## Minimal deployment checklist (once the above is in place)

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
export DJANGO_SECRET_KEY=<a real random secret>
export DJANGO_ALLOWED_HOSTS=yourdomain.com

python manage.py check --deploy   # verifies the security checklist
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_roles
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Why this scope, not more

Building a fully containerized, task-queued, object-storage-backed
deployment pipeline is real, valuable work — but it's infrastructure
engineering, not the data science / Django / ML syllabus this project
demonstrates. Documenting exactly what's missing and why (rather than
either skipping this section or building infrastructure the project
doesn't need) is the more honest choice for a college submission, and is
exactly the kind of thing to bring up proactively in a viva if asked
"is this production-ready?"
