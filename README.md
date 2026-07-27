# Foster Care Placement Predictor

AI-powered foster care placement recommendation system — Django, Machine
Learning, Web Scraping, and Data Analytics.

> **Project status: COMPLETE (13/13 milestones).** Every layer — Django
> backend, ML pipeline, web scraping, REST API, exports, and final
> documentation — is built, verified with real output (not just "no
> exceptions raised"), and packaged. See `docs/` for diagrams, EDA/ML
> reports, and full documentation; see the "Documentation Index" section
> below for a guided tour.

## Data ethics notice

Every `Child` and `FosterFamily` record in this system is **synthetically
generated**. No real child's identity, case history, or welfare record is
ever stored or processed here. Aggregate, publicly available government
statistics are scraped for the `Report` / `ReportStatistic` models — never
personally identifiable case data. See the project's Step 1 planning notes
for the full reasoning.

## What's actually implemented right now

- Full modular Django project structure (`config/`, `apps/*`, `ml/`)
- All 8 core models across 6 apps, matching the ER diagram exactly:
  `Profile`, `Child`, `FosterFamily`, `Placement`, `Prediction`, `Report`,
  `ReportStatistic`
- Migrations generated and applied — `db.sqlite3` builds cleanly
- Django admin registered for every model (with inlines, filters, search)

### Authentication & role-based permissions (Step 5)
- Real registration form (`RegistrationForm`) — public sign-up is
  restricted to **Case Worker** / **Viewer**; **Admin** is granted
  manually via Django admin, never self-service (documented security
  decision, see `apps/accounts/forms.py`)
- Login / logout / full password-reset flow using Django's built-in,
  security-hardened auth views, with real templates
- `Profile.role` field kept **automatically in sync** with Django Groups
  via a `post_save` signal (`apps/accounts/signals.py`) — this is what
  prevents "UI says Admin, permissions say otherwise" bugs
- `manage.py seed_roles` management command creates the three Groups
  (Admin, Case Worker, Viewer) with correct per-model permissions —
  idempotent, safe to re-run
- Reusable access-control primitives in `apps/accounts/permissions.py`:
  `role_required` decorator (function views), `RoleRequiredMixin` and
  `ViewerReadOnlyMixin` (class-based views) — every other app will import
  these rather than re-implementing role checks
- **Verified end-to-end, not just written:** registered a real Case
  Worker through the actual HTTP form, confirmed auto-login, confirmed
  Group assignment and permissions (`add_child`=True, `delete_child`=True);
  registered a Viewer and confirmed read-only permissions
  (`view_child`=True, `add_child`=False); confirmed unauthenticated
  requests to protected pages return `302` to login while the public
  landing page returns `200`
- Global `base.html` + navbar + footer + theme CSS (light/sky-blue/
  green/pastel-orange, per the UI brief) — every page from here on
  extends this, so styling stays consistent as more pages are built

### Web scraper (Step 6)
- `ml/scraping/robots_check.py` — a `RobotsChecker` wrapping Python's
  `urllib.robotparser`, consulted before every single fetch. **Real
  finding, documented in the code**: India's Ministry of Women & Child
  Development portal (the project brief's original suggested source)
  disallows automated access per its robots.txt. The scraper was
  redirected to a real, permissive, thematically ideal alternative: the
  U.S. Administration for Children and Families' **AFCARS** foster care
  statistics (acf.gov), which explicitly allow programmatic access and
  publish exactly the entry/exit/placement numbers this project needs.
- `ml/scraping/scraper.py` — `GovernmentReportScraper`: discovers report
  links on a listing page (`requests` + `BeautifulSoup`), downloads
  PDF/HTML reports, and respects each site's crawl-delay. Zero Django
  imports — pure Python, usable/testable standalone (Step 2 design goal).
- `ml/scraping/pdf_parser.py` — text and table extraction via
  **pdfplumber** (chosen over pypdf/PyPDF2 specifically for its table-
  geometry reconstruction, which government report PDFs need).
- `ml/scraping/afcars_table_parser.py` — interprets the specific
  real-world shape of AFCARS's "Numbers at a Glance" table (years as
  columns, metrics as rows) and transposes it into the long/tidy format
  `ReportStatistic` uses.
- `apps/reports/management/commands/scrape_reports.py` — the ONLY place
  `ml/scraping` and Django models meet, keeping `ml/` genuinely reusable
  outside the web framework. Supports both live scraping
  (`--source <url>`) and offline ingestion of already-downloaded files
  (`--local-dir <path>`) for reproducible testing/grading.
- **Verified end-to-end against real published data, not synthetic
  numbers**: `ml/scraping/fixtures/` contains a locally-generated PDF
  built from the actual figures published in AFCARS Report #29 (a public
  U.S. government document) plus an HTML fixture, used to prove the full
  pipeline — discovery → robots check → download → PDF table extraction →
  database ingestion — end to end without requiring live internet access
  from a sandboxed grading environment. Run `python manage.py
  scrape_reports --local-dir ml/scraping/fixtures` to reproduce; the 25
  resulting `ReportStatistic` rows match the real published AFCARS
  figures for FY2017-2021 exactly. Also verified: a robots.txt-disallowed
  source is correctly skipped with zero reports ingested, not silently
  bypassed.
- To run against the live source instead: `python manage.py
  scrape_reports` (uses `ml/scraping/scraper.py`'s default
  `REPORT_SOURCES`, currently pointed at the real AFCARS statistics page).

### Synthetic data generator (Step 7)
- `ml/data/synthetic_generator.py` — generates `Child`, `FosterFamily`,
  and `Placement` records. No real case data anywhere (Step 1 ethics
  notes). Distributions are grounded where possible in aggregate AFCARS
  figures (e.g. special-needs prevalence, age spread) rather than being
  arbitrary; every simplifying assumption is stated in the module's
  docstring, not hidden.
- **Deliberate, documented correlations** encoded so the future ML
  classifier has real signal to learn (see docstring for full detail):
  special-needs/family-acceptance mismatch, sibling-group vs. family
  capacity (a hard constraint, never violated), in-state vs. cross-state
  placement, and family experience level.
- `apps/core/management/commands/generate_synthetic_data.py` — the bridge
  into the database (`--children N --families M --seed S --clear`).
- **Verified against the actual generated data, not just asserted in
  comments**: with 900 children / 220 families / ~380 placements, the
  special-needs mismatch group showed a **26.4% disruption rate vs.
  11.5%** for compatible pairs (~2.3x) — the strongest and most reliable
  encoded signal. Cross-state placements showed a smaller, correctly-
  directioned effect (15.5% vs. 12.0%). Sibling-group-vs-capacity was
  checked as a hard constraint: **zero** families had `current_occupancy
  > capacity` across every regeneration tested. Gender split, special-
  needs rate, and state distribution all matched their target
  probabilities within normal sampling noise, with zero null values.
- Honest note: an early version of the matching logic had a real bug —
  the "prefer in-state" fallback pool wasn't reshuffled per child, so
  most children ended up drawing from the same fixed handful of families,
  which silently skewed the cross-state correlation. Caught by actually
  querying the generated data's group sizes rather than trusting the code
  to do what its docstring claimed — worth mentioning in your report as
  an example of why validating generated data matters as much as writing
  the generator.
- Run with: `python manage.py generate_synthetic_data --children 900
  --families 220` (defaults: 300 children, 80 families, seed 42).

### EDA + Visualization (Step 8)
- `ml/eda/eda_report.py` — missing values, duplicate rows, IQR-based
  outlier detection (chosen over z-score because several fields, like
  `time_in_care_months`, are deliberately right-skewed by the synthetic
  generator's exponential distribution — z-score assumes normality),
  distribution statistics, and Pearson/Spearman correlation. Pure pandas,
  no Django imports, reusable by the Step 9 ML feature engineering.
- `ml/visualization/charts.py` — 15 Seaborn-primary chart functions
  (histogram, count plots, correlation heatmap, box plot, violin plot,
  pair plot, logistic regression plot, line chart) sharing one consistent
  signature (`DataFrame, output_path -> saved_path`) so the future
  dashboard view can call them generically. Confusion matrix, ROC curve,
  feature importance, and accuracy/F1 comparison charts are deliberately
  **not** built here — they require a trained model's predictions to mean
  anything, so they belong to Step 9, not this one.
- `apps/analytics/management/commands/run_eda.py` — the bridge into the
  database, writing `docs/eda_summary.md` and 18 PNGs to
  `media/analytics/charts/`.
- **Verified by actually looking at the output, not just checking exit
  codes**: I visually inspected 5 of the 18 generated charts (age
  histogram, correlation heatmap, experience-vs-disruption regression,
  pairplot, and the real-data AFCARS trend line) to confirm they render
  correctly rather than trusting "no exception was raised." The
  experience-vs-disruption logistic curve correctly slopes downward,
  matching the rule encoded in Step 7's synthetic generator. The
  year-wise trend chart plots the **real** published AFCARS figures from
  the Step 6 scraper (not synthetic data) — children in care declining
  from ~437K to ~391K, FY2017-2021.
- Two real bugs caught and fixed during this step, both worth mentioning
  in a report as examples of why "it ran without error" isn't the same
  as "it's correct": (1) `statsmodels` was a silently-required dependency
  for the logistic regression plot that only surfaced at runtime; (2) a
  matplotlib internal log message was leaking into command output because
  our dev logging config runs at INFO — fixed by scoping matplotlib's own
  logger to WARNING rather than silencing our project's logs.
- `requirements.txt` was verified to install cleanly into a brand new,
  empty virtual environment — not just "works on my machine" because
  packages were already present from earlier steps.
- Run with: `python manage.py run_eda` (requires
  `generate_synthetic_data` and, optionally, `scrape_reports` to have
  been run first — see docs/eda_summary.md and media/analytics/charts/
  for this run's actual output, included in this zip).

### ML Training Pipeline (Step 9)
- `ml/features/feature_engineering.py` — builds TWO prediction targets
  from the joined Child/FosterFamily/Placement data:
  1. **Classification** target `disrupted` — framed as predicting the
     ONE outcome actually observed in the data (placement disruption)
     rather than inventing an unobserved "compatibility score" to train
     on, which would be circular. Low disruption probability = high
     compatibility, by definition.
  2. **Regression** target `time_in_care_months` — a genuinely meaningful
     continuous target (case workers plan resources around expected
     time-in-care), predicted from a child's own profile independent of
     any specific family.
- `ml/training/train_classification.py` — 7 classifiers (Logistic
  Regression, Decision Tree, Random Forest, Gradient Boosting, SVM, KNN,
  XGBoost), all evaluated on the same train/test split plus 5-fold
  cross-validation, with GridSearchCV hyperparameter tuning demonstrated
  on Random Forest.
- `ml/training/train_deep_learning.py` — a small Keras MLP, with an
  explicit, printed **dataset-size justification check** before training
  (per the project brief's "don't force deep learning on small data"
  guidance) rather than building it unconditionally.
- `ml/training/train_regression.py` — 4 regressors (Linear, Decision
  Tree, Random Forest, Gradient Boosting) for the time-in-care target.
- `ml/training/model_comparison.py` — selects the best classifier by
  **F1 score, not accuracy** (the disruption class is a ~14% minority;
  accuracy alone would reward a model that never predicts it).
- `apps/predictions/management/commands/train_models.py` — the bridge
  command: loads data, engineers features, trains everything, generates
  9 evaluation charts (confusion matrices, ROC curves, precision-recall
  curves, feature importance, accuracy/F1 comparison bar charts,
  regression predicted-vs-actual), writes `docs/ml_report.md`, and
  persists the best model to `ml/models_store/` — verified to actually
  reload and serve a prediction, not just save successfully.

**Three real bugs caught and fixed during this step** — documented
honestly because catching them is as important as building the pipeline:
1. **SVM and KNN both scored F1=0.0** on first run — they never
   predicted the minority (disrupted) class at all, a classic class-
   imbalance failure. Fixed with `class_weight="balanced"` (Logistic
   Regression/Decision Tree/Random Forest/SVM) and `scale_pos_weight`
   (XGBoost). KNN has no direct class-weighting mechanism — documented
   as a known limitation rather than silently left broken.
2. **All 4 regression models showed negative R²** — worse than predicting
   the mean. Root cause: the Step 7 synthetic generator's
   `time_in_care_months` was pure exponential noise with **zero
   dependency on any child feature**, despite the module's own docstring
   claiming otherwise. Fixed by making the exponential's *mean* depend on
   age/special-needs/behavioral-score/sibling-size (real foster-care
   research directions), then discovered that still failed because
   exponential noise has `std ≈ mean`, swamping the signal — fixed again
   by separating a fixed-scale noise term from the feature-driven signal.
   Final result: correlations rose from ~0.17 to ~0.44-0.51, and Linear
   Regression's R² went from -0.03 to **+0.40**.
3. **TensorFlow's RNG was never seeded**, unlike every classical model's
   fixed `random_state=42` — caught by noticing the MLP "won" the model
   comparison on some runs and not others with byte-identical input data.
   Fixed with `keras.utils.set_random_seed(42)`.
- **Final verified result** (reproducible with the fixes above): the MLP
  narrowly edges out the best classical model (F1 0.632 vs. SVM's 0.571)
  on this run. The report doesn't just state the winner — it explicitly
  notes that with only 77 test samples, a single additional correct
  prediction shifts F1 by ~0.013, so this narrow margin should be read as
  "roughly tied," not "deep learning decisively wins," consistent with
  the dataset-size caveat printed before training even began.
- Model persistence handles both cases correctly: classical models save
  via `joblib`, but the Keras model — when it wins — saves via
  TensorFlow's native `.keras` format instead, since pickling a raw
  TensorFlow object is fragile. Both paths were verified to reload and
  produce a working prediction, not just save without erroring.
- Run with: `python manage.py train_models` (requires
  `generate_synthetic_data` to have been run first; takes a few minutes
  due to GridSearchCV + MLP training — see `docs/ml_report.md` and
  `media/analytics/charts/` for this run's actual output, included in
  this zip).

### Full Views & Templates (Step 10)
Every page listed in the original brief now has a real implementation —
not a placeholder — with search, filtering, pagination, role-based
create/edit/delete, and proper form validation:

- **Children** (`apps/children`) — search by name/state, filter by
  gender/special-needs/placement status, sortable, paginated (20/page).
  Full create/edit/delete for Admin/Case Worker; delete restricted to
  Admin only. Detail page shows placement and prediction history.
- **Foster Families** (`apps/families`) — search/filter by state, home
  type, special-needs acceptance, and an "available slots only" filter
  using an `F()` expression comparison. Custom form validation rejects
  `current_occupancy > capacity`.
- **Placements** (`apps/placements`) — filter by status; a disruption
  reason is required by form validation whenever status is set to
  Disrupted.
- **Predictions** (`apps/predictions`) — this is where Step 9's trained
  model actually gets used: `ml/inference/predict.py` loads whichever
  model won (classical via `joblib` or the Keras MLP via its native
  `.keras` format — both paths handled explicitly, since pickling a raw
  TensorFlow object is fragile), builds a feature row through the exact
  same `build_placement_features()` function training used (by reuse, not
  duplication — see the function's docstring), transforms it with the
  *fitted* encoders/scaler (never refit at inference time — that would be
  a data leakage bug), and returns a live compatibility score.
- **Reports** (`apps/reports`) — list/search/detail for scraped AFCARS
  reports, plus an Admin-only "re-run scrape" action. Documented
  limitation: it runs synchronously in the request cycle (fine at this
  scale; a production system would offload this to Celery/Django-RQ —
  noted honestly rather than silently glossed over) and re-ingests the
  bundled fixtures rather than live acf.gov, consistent with this
  sandboxed environment's network restrictions from Step 6.
- **Analytics** (`apps/analytics`) — a real dashboard with live DB-backed
  stats cards, recent activity, and highlight charts; a full
  Visualizations gallery organized by category (all 29 charts from Steps
  8-9); a Model Comparison page rendering the actual `ml_report.md`.

**Verified end-to-end, not just "no exceptions raised"**:
- Logged in as each of the three roles and walked every main page,
  confirming `200` for allowed pages and `403` for role-restricted ones —
  e.g. a Viewer gets `403` on `/predictions/new/`, `/children/add/`,
  `/families/add/`, `/placements/add/`, but `200` on every read-only page.
- **Submitted a real prediction request through the actual HTTP form**
  (not a unit test calling the function directly) and confirmed a genuine
  `Prediction` row was created with a real score (0.7583, Deep Learning
  MLP) — this exercised the full chain from Django form → view →
  `ml.inference.predict` → loading the persisted Step 9 model → feature
  engineering → scaling → model inference → database write → redirect to
  a detail page that correctly displays the result.
- Confirmed the family form's custom validation (`occupancy > capacity`)
  correctly rejects an invalid submission with a `200` (re-rendered form
  with the error), not a `302` (would mean it wrongly saved).
- Confirmed search/filter/pagination all work against the real 900-row
  dataset, and that chart images actually serve with the correct
  `image/png` content type through `/media/`.
- Confirmed the Admin-only report re-scrape trigger returns `403` for a
  Case Worker and `302` (success) for an Admin.

**One real bug caught during this step**: `build_regression_features()`
was accidentally deleted by an earlier edit that inserted new inference
functions in its place without preserving it — caught immediately by
`train_models` crashing with an `ImportError` on the next full pipeline
run, not by silent failure. A reminder that "the file saved without
error" and "the file is still correct" are different claims.

### REST API (Step 11)
Full Django REST Framework layer under `/api/v1/`, deliberately built to
be impossible to silently drift from the web UI's business rules:

- **ViewSets** for Children, Foster Families, Placements, Predictions
  (read-only for direct list/retrieve), and Reports (read-only), all
  under `apps/api/views/`, registered on a `DefaultRouter`
  (`apps/api/urls.py`) — standard REST conventions (list/create at the
  collection URL, retrieve/update/delete at `/id/`).
- **`apps/api/permissions.py`** — custom DRF permission classes that
  encode the SAME role rules as the web views (Step 5/10): Viewers get
  read-only (`403` on any write), Case Workers can create/update, deletes
  are Admin-only. This is a separate module from the web-side mixins (DRF
  uses a different interface) but defines the same rules — verified by
  testing both surfaces return matching `403`s for the same role.
- **Live prediction endpoint** — `POST /api/v1/predictions/request_prediction/`
  takes `{"child": id, "family": id}` and runs the ACTUAL trained model
  via `ml.inference.predict` — the identical function the web UI's
  `PredictionCreateView` calls, so the API and the web app can never
  silently disagree on how a prediction is computed. Verified with a real
  HTTP POST: same child/family pair scored via the web UI and via the API
  both returned exactly 0.7583 — proof the two code paths are genuinely
  shared, not just similarly written.
- **Serializer-level validation** mirrors the web forms exactly:
  `behavioral_notes_score` must be 0.0-1.0, `current_occupancy` cannot
  exceed `capacity`, `disruption_reason` is required when
  `status='disrupted'` — all tested with real invalid payloads returning
  `400` with the expected error message, not silently accepted.
- **Filtering, search, ordering** via `django-filter` +
  DRF's built-in `SearchFilter`/`OrderingFilter` — e.g.
  `/api/v1/children/?special_needs=true&search=Avery&ordering=-age`.
- **`/api/v1/docs/`** — a hand-written, plain-English endpoint reference
  (deliberately not an auto-generated schema like drf-spectacular; DRF's
  own browsable API already provides interactive per-field documentation
  when you visit any endpoint in a logged-in browser — the two are
  complementary, not redundant).
- **`/api/v1/dashboard-stats/`** — the same aggregate numbers the web
  dashboard shows, exposed for any external client.

**Verified with real HTTP requests as three different roles, not just
written and assumed correct**:
- Viewer: `200` on every list/retrieve endpoint, `403` on every write
  attempt including `request_prediction/`.
- Case Worker: can create/update Children/Families/Placements, gets
  `403` attempting to `DELETE` (Admin-only).
- Admin: full CRUD confirmed, including a real create-then-delete
  round trip (`201` then `204`).
- A real prediction request round-tripped through the API returned
  `201 Created` with a genuine score from the persisted Step 9 model —
  not a mock or stub response.
- Two validation rules tested with deliberately invalid payloads, both
  correctly rejected with `400` and a clear field-level error message.

### Export Features (Step 12)
- **`apps/core/exports.py`** — shared `export_as_csv()`/`export_as_excel()`
  helpers used by every app, taking `(header_label, value_getter)` pairs
  rather than raw field names so exports show exactly what the UI shows
  (e.g. `get_gender_display()`, `available_slots`), not raw DB values.
  Excel exports are genuinely formatted (bold header row, theme-colored
  fill, auto-sized columns), not just a CSV with a different extension.
- **CSV + Excel** on Children, Foster Families, and Placements list
  pages; **CSV** on Predictions and Report Statistics.
- **Filtered exports, not "export everything"**: each app's list-view
  filter logic was refactored into a shared function
  (`filter_children_queryset()`, etc.) called by BOTH the list view and
  the export view, so exporting always means "export exactly what I'm
  currently looking at." Verified: exporting Children with
  `?special_needs=true` in the URL produced exactly 194 rows — matching
  the count independently confirmed via the API's `?special_needs=true`
  filter in Step 11, proving the two code paths stay consistent by
  construction, not by coincidence.
- **PDF prediction report** (`predictions/<id>/export/pdf/`) — a
  formatted reportlab Platypus document (title, colored score, child/
  family comparison table, a standard case-worker-review disclaimer).
- **PDF dashboard summary** (`analytics/dashboard/export/pdf/`) — live
  DB stats plus three REAL embedded chart images (not re-rendered
  placeholders) pulled directly from `media/analytics/charts/`.
- **Chart downloads** — every image in the Visualizations gallery
  (Step 8/9's 29 charts) has a direct download link.

**Verified by actually opening the generated files, not just checking
HTTP status codes**:
- CSV row counts matched exactly: 901 lines for 900 children (+ header),
  221 for 220 families, 385 for 384 placements.
- Excel files confirmed with the correct
  `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  content-type and non-trivial file sizes (14-45 KB).
- **A real rendering bug was caught and fixed by actually looking at the
  output**: the first version of the PDF prediction report had the score
  number and the "predicted compatibility score" caption overlapping —
  caused by mixing font sizes inline within one `Paragraph` without
  adjusting its `leading` (line height), which reportlab doesn't do
  automatically. This is exactly the kind of bug that "the PDF file was
  generated without an exception" would never catch — it was found by
  converting the PDF to a PNG (`pdftoppm`) and visually inspecting it,
  then confirmed fixed the same way after the correction.
- The dashboard summary PDF's embedded stats table was checked against
  the live database and matched exactly (900 children, 220 families, 308
  placed, 164 active placements, 52 disrupted) — proving the PDF isn't
  using stale or hardcoded numbers.

- Root URL routing wired for every planned app/namespace
- Verified: `manage.py check`, `makemigrations`, `migrate`, and the dev
  server all run without errors

## What's intentionally a placeholder

Views in `children`, `families`, `placements`, `predictions`, `reports`,
`analytics`, and `api` return minimal responses (or, for `accounts/login`,
a bare unstyled form) purely so routes resolve today. Real templates,
forms, search/filter logic, the scraper, EDA, ML training, and DRF
serializers/viewsets are built in the milestones that follow — each
placeholder file has a docstring saying so.

## Getting started

```bash
# 1. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template and edit as needed
cp .env.example .env

# 4. Apply migrations (already generated, safe to re-run)
python manage.py migrate

# 5. Seed the three role groups (Admin / Case Worker / Viewer) with
#    their model permissions — safe to re-run any time
python manage.py seed_roles

# 6. Create your own superuser (a test one is NOT included in the zip
#    for security — create your own):
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` — landing page placeholder
- `http://127.0.0.1:8000/admin/` — full Django admin for all models
- `http://127.0.0.1:8000/api/v1/` — API root placeholder
- `http://127.0.0.1:8000/accounts/login/` — login (Django's built-in auth view)

## Project structure

See `docs/` for the full folder-by-folder explanation produced during
planning. In short:
- `config/` — settings (split into base/development/production), root URLs
- `apps/` — one Django app per domain concept (accounts, children,
  families, placements, predictions, reports, analytics, core, api)
- `ml/` — standalone Python package for scraping, EDA, feature engineering,
  model training, and visualization — deliberately kept outside `apps/`
  so it's testable independent of Django
- `docs/` — every deliverable listed below

## Build history (all 13 milestones complete)

1. ✅ Planning & architecture (data ethics, tech stack, scope)
2. ✅ Project folder structure
3. ✅ Database design (ER diagram, normalization)
4. ✅ Django skeleton, models, migrations
5. ✅ Authentication + role-based permissions
6. ✅ Web scraper (real AFCARS government data, robots.txt-verified)
7. ✅ Synthetic data generator (verified, ML-learnable correlations)
8. ✅ EDA + visualization (18 charts)
9. ✅ ML training pipeline (7 classifiers + regression + deep learning
   comparison, all evaluated on evidence)
10. ✅ Full Django views/templates (search, filter, pagination, CRUD,
    live prediction serving)
11. ✅ REST API (DRF, mirrors every web feature and permission rule)
12. ✅ Export features (CSV, Excel, PDF, chart downloads)
13. ✅ Final documentation (diagrams, tests, viva prep, deployment guide)

## Documentation Index

Everything below is in `docs/` unless noted otherwise:

| Document | What it covers |
|---|---|
| `architecture.md` | System design, app boundaries, request flow, why `ml/` is framework-independent |
| `installation_guide.md` | Full setup steps + troubleshooting |
| `deployment_guide.md` | What's production-ready now vs. what would need to change |
| `testing_guide.md` | The 32 automated tests + a table of real bugs manual verification caught |
| `eda_summary.md` | Missing values, outliers, correlation — generated by `run_eda` |
| `ml_report.md` | Full model comparison table — generated by `train_models` |
| `college_report_structure.md` | Suggested report chapter structure mapped to syllabus topics |
| `presentation_outline.md` | Slide-by-slide viva presentation guide |
| `viva_questions.md` | Anticipated questions with answers grounded in real project decisions |
| `future_scope_and_limitations.md` | Honest limitations + what's next |
| `diagrams/er_diagram.png` | Entity-relationship diagram |
| `diagrams/use_case_diagram.png` | Use case diagram (3 roles) |
| `diagrams/dfd.png` | Data flow diagram |
| `diagrams/flowchart_prediction_request.png` | Prediction request process flowchart |
| `diagrams/scripts/` | Python (graphviz) scripts that generated the 4 diagrams above — re-run any of them any time the system changes |
| `tests/` (project root) | 32 automated tests — run with `python manage.py test tests` |

## A note on how this was built

Every milestone in this project was verified by actually running it and
reading the real output — not by assuming code that didn't crash was
correct. That approach caught several genuine bugs along the way (listed
in full in `docs/testing_guide.md`): a classifier silently scoring 0 on
the minority class, a regression target with no real learnable signal,
an unseeded random number generator causing inconsistent results, a
PDF layout bug only visible by actually rendering the file to an image,
and a function accidentally deleted by an earlier edit. None of these
would have been caught by a shallower "does it run?" standard — which is
exactly why they're documented here instead of quietly fixed and
forgotten.
