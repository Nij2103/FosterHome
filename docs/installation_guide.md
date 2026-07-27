# Installation Guide

## Prerequisites

- Python 3.11+ (developed and tested against 3.12)
- `pip`
- ~2 GB free disk space (TensorFlow-CPU and its dependencies are the
  largest single install)
- Graphviz system package (`dot`), only needed if you want to regenerate
  the diagrams in `docs/diagrams/` — not required to run the application
  itself. Install via `apt install graphviz` (Linux) or `brew install
  graphviz` (macOS) if needed.

## Step-by-step setup

```bash
# 1. Extract the zip and enter the project directory
cd foster_care_predictor

# 2. Create and activate a virtual environment (strongly recommended —
#    this project pins/depends on a specific set of package versions)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
# This installs Django, DRF, the full data-science stack (pandas, numpy,
# scikit-learn, xgboost, seaborn, matplotlib, statsmodels), TensorFlow-CPU,
# the scraping stack (requests, beautifulsoup4, pdfplumber), and export
# libraries (openpyxl, reportlab). Expect this step to take a few minutes
# — TensorFlow-CPU alone is a substantial download.

# 4. Copy the environment template and edit if needed (defaults work
#    fine for local development)
cp .env.example .env

# 5. Apply database migrations
python manage.py migrate

# 6. Seed the three role groups (Admin / Case Worker / Viewer) with
#    their model permissions — safe to re-run any time
python manage.py seed_roles

# 7. Create your own superuser account
python manage.py createsuperuser

# 8. Generate the synthetic dataset the rest of the pipeline depends on
python manage.py generate_synthetic_data --children 900 --families 220

# 9. (Optional) Ingest the bundled AFCARS report fixtures — populates
#    the Reports section and the "real government data" trend charts
python manage.py scrape_reports --local-dir ml/scraping/fixtures

# 10. (Optional but recommended) Run the EDA pipeline — generates
#     docs/eda_summary.md and 18 charts under media/analytics/charts/
python manage.py run_eda

# 11. (Optional but recommended) Train the ML models — takes a few
#     minutes (GridSearchCV + a Keras MLP). Generates docs/ml_report.md,
#     9 more evaluation charts, and saves the best model to
#     ml/models_store/. The Predictions feature won't work without this.
python manage.py train_models

# 12. Run the development server
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/` and log in with the superuser you
created (or register a new Case Worker/Viewer account — Admin accounts
are intentionally not self-service; see the Security notes in the main
README).

## Running the automated tests

```bash
python manage.py test tests
```

32 tests covering models, role-based view access, the REST API, and the
ML feature-engineering logic. Takes about a minute (most of that is
Django's test-database setup plus one TensorFlow import).

## Common issues

**`ModuleNotFoundError` for a specific package** — you're likely not
inside the virtual environment. Run `source venv/bin/activate` (or the
Windows equivalent) again and retry `pip install -r requirements.txt`.

**Predictions page says "no trained model found"** — you skipped step 11
(`train_models`). This is expected; the app degrades gracefully (a clear
message, not a crash) rather than assuming a model exists.

**Charts/dashboard look empty** — you skipped steps 8, 10, and/or 11.
The dashboard and Visualizations page read from `media/analytics/charts/`,
which only exists after `run_eda` and `train_models` have actually run.

**`scrape_reports` (without `--local-dir`) doesn't return anything /
times out** — this points at the real acf.gov AFCARS statistics page,
which requires normal internet access. It will not work from a
network-sandboxed environment. Use `--local-dir ml/scraping/fixtures`
for a fully offline demonstration using the bundled fixture (built from
real, published AFCARS figures — see `docs/eda_summary.md` and the main
README's Step 6/7 notes for the full story).

**TensorFlow install is slow / very large** — this is normal; TensorFlow-
CPU and its transitive dependencies (numpy pins, protobuf, etc.) are
the single largest piece of `requirements.txt`. If you don't need to
retrain models (e.g. you're only reviewing the code), you can comment
out `tensorflow-cpu` in `requirements.txt` — everything except
`train_models` and the deep-learning comparison will still work.
