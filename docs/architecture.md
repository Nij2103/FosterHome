# Architecture

## High-level overview

```
Presentation:  Django templates + Bootstrap 5, role-aware navbar
                    |
Web layer:     Django apps (accounts, children, families, placements,
               predictions, reports, analytics, core, api)
                    |
Data science:  ml/ package — scraping, synthetic data, EDA,
               visualization, feature engineering, training, inference
               (deliberately independent of Django — see below)
                    |
Persistence:   SQLite via Django ORM; trained model artifacts in
               ml/models_store/; generated charts in
               media/analytics/charts/
```

## Why `ml/` is a separate package, not a Django app

This is the single most consequential architectural decision in the
project (made in Step 2, held to for the rest of the build). Every
function in `ml/eda/`, `ml/features/`, `ml/training/`,
`ml/visualization/`, and `ml/scraping/` takes and returns plain Python
objects (pandas DataFrames, numpy arrays) — no Django imports anywhere
in that tree. Consequences of this, all realized during the actual
build:

- **Testable without a database.** `tests/test_ml_pipeline.py` tests
  `build_placement_features()` with hand-built DataFrames in
  milliseconds — no Django test database, no fixtures.
- **Training and inference can't silently drift apart.** The Django
  prediction views (`apps/predictions/views.py`, `apps/api/views/
  predictions_views.py`) both call the exact same
  `ml.inference.predict.predict_compatibility()` function, which itself
  calls `build_single_pair_features()`, which wraps and reuses
  `build_placement_features()` — the same function `train_models` uses.
  This was verified concretely in Step 11: the same child/family pair
  scored identically (0.7583) through the web UI and the API.
- **A real bug was caught faster because of this separation**: in Step
  9, `build_regression_features()` was accidentally deleted; because
  `ml/` has no Django coupling, the very next `train_models` run failed
  immediately and specifically with an `ImportError`, not a confusing
  Django request-cycle traceback.

## Django app boundaries

| App | Responsibility | Owns models? |
|---|---|---|
| `accounts` | Auth, roles, permissions primitives | `Profile` |
| `children` | Child records, CRUD, export | `Child` |
| `families` | Foster family records, CRUD, export | `FosterFamily` |
| `placements` | Placement records, CRUD, export | `Placement` |
| `predictions` | Prediction requests/results, PDF export | `Prediction` |
| `reports` | Scraped report storage, CSV export | `Report`, `ReportStatistic` |
| `analytics` | Cross-app dashboards, charts, ML report display | none (queries others) |
| `core` | Landing/about/contact, shared cross-app management commands | none |
| `api` | DRF serializers/viewsets/permissions mirroring the web apps | none |

`analytics` and `api` deliberately own no models — they're consumers of
the other apps' data, which is what keeps them from becoming a dumping
ground that couples every other app together.

## Request flow: a prediction, end to end

1. Case Worker submits child + family via the web form
   (`apps/predictions/views.py: PredictionCreateView`) or the API
   (`apps/api/views/predictions_views.py: request_prediction`).
2. Both call `ml.inference.predict.predict_compatibility(child, family)`.
3. That function loads the persisted model bundle from
   `ml/models_store/` (`load_best_model()` — handles both the
   `joblib`-pickled classical-model path and TensorFlow's native
   `.keras` format explicitly, since pickling a raw Keras model is
   fragile).
4. `build_single_pair_features()` wraps the single child/family pair in
   one-row DataFrames and calls the SAME `build_placement_features()`
   training used.
5. `transform_classification_features()` applies the *already-fitted*
   encoders/scaler saved during training — never refit at inference
   time, which would be a data-leakage bug.
6. The model predicts a disruption probability; the view/API inverts it
   to a compatibility score, saves a `Prediction` row, and renders/
   returns the result.

## Data pipeline (offline, via management commands)

```
scrape_reports  ─────────────────────────►  Report / ReportStatistic
                                                     │
generate_synthetic_data  ───────────►  Child / FosterFamily / Placement
                                                     │
run_eda  ◄───────────────────────── (reads both of the above)
   │
   └──► docs/eda_summary.md + 18 charts

train_models  ◄──────────────────── (reads Child/FosterFamily/Placement)
   │
   ├──► docs/ml_report.md + 11 evaluation charts
   └──► ml/models_store/ (best model + preprocessing)
```

Each command is independently re-runnable and safe to re-run (documented
per-command in the main README) — there's no hidden ordering requirement
beyond "generate data before you can train on it."

## Security model

Three roles (`Admin`, `Case Worker`, `Viewer`), enforced at both the UI and server layers:

### Role Hierarchy & Assignment Rules
- **Self-Registration (Viewer Default)**: Public self-registration (`RegistrationForm`) strictly assigns `Profile.Role.VIEWER`. Public users cannot select `Case Worker` or `Admin` roles, closing off privilege escalation vulnerabilities.
- **Admin-Panel Role Promotion**: Role elevation to `Case Worker` or `Admin` is performed exclusively by an existing Admin through the Django Admin interface.
- **Viewer Access**: Viewers have full read-only access across all records (children, families, placements, reports) AND are permitted to run ML prediction requests (`PredictionCreateView`). Viewers are prohibited from mutating operational records.
- **Admin & Case Worker Access**: Full Create, Update, and Delete access across all records.

### Enforcement Architecture
1. **Template Gating**: Cleanly hides mutation buttons from Viewers using the `{% load role_tags %}` template filter (`{% if request.user|can_edit %}`).
2. **Server-Side Authorization**: Django view mixins (`RoleRequiredMixin`, `ViewerReadOnlyMixin`, `@role_required`) and DRF permission classes (`IsAdminOrCaseWorkerOrReadOnly`) return `HTTP 403 Forbidden` if a Viewer attempts direct URL access to mutation endpoints.
3. **Synchronized Role Architecture**: A `post_save` signal on `Profile` (`apps/accounts/signals.py`) automatically synchronizes `Profile.role` with Django `Group` memberships (`Admin`, `Case Worker`, `Viewer`) seeded by `manage.py seed_roles`.

