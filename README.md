# Foster Care Placement Predictor

An intelligent decision-support web application that assists child welfare professionals, caseworkers, and administrators in matching foster children with compatible foster families using machine learning models, explainable AI (SHAP), and domain-driven hard constraints.

> **Data Ethics Notice**: Every `Child` and `FosterFamily` record in this demonstration system is synthetically generated. No real child's identity or sensitive child welfare case record is stored or processed here.

---

## Key Features

- **Machine Learning Placement Compatibility Engine**: Predicts placement success probability (0–100%) using trained classification algorithms (`RandomForestClassifier`, `GradientBoostingClassifier`, `LogisticRegression`).
- **Explainable AI (XAI)**: Generates feature attribution breakdowns (SHAP) so caseworkers can see exactly which factors contribute positively or negatively to a compatibility score.
- **Smart Candidate Matching**: Automated lookup engine (`/predictions/matching/`) that filters candidates by hard domain constraints (family capacity, special needs support, language, age preference) combined with ML suitability thresholds.
- **Placement Lifecycle Management**: Redesigned 3-section placement workflow (Assignment, Details, Closure). Automatically excludes children with active placements and families at full capacity. Restricts completion/disruption end-states to update mode. Enforces strictly valid date ranges (`end_date > start_date`).
- **Data Isolation & Role-Based Access Control (RBAC)**: Supports 3 distinct user roles:
  - **Viewer**: Self-registered read-only access + prediction requests. Data isolated to families/placements created by the logged-in user.
  - **Case Worker**: Full CRUD access to managing children, foster families, and placement lifecycles.
  - **Administrator**: Full administrative control, system metrics, and role management.
- **Indian Contact Standard & Validation**: Enforces valid 10-digit Indian phone numbers starting with **6, 7, 8, or 9** formatted as `+91-XXXXX-XXXXX`.
- **Pure CSS & Modular JS Architecture**:
  - **100% Inline CSS Removed**: All styling is consolidated into [`static/css/style.css`](static/css/style.css).
  - **100% External JS Modules**: Clean event-driven JavaScript extracted into [`static/js/`](static/js/) (`child_form.js`, `placement_form.js`, `prediction_form.js`, `reports.js`).
- **REST API Subsystem**: Full REST API built with Django REST Framework (`/api/v1/`) featuring interactive API documentation.

---

## Technology Stack

- **Backend Framework**: Python 3.14 + Django 6.0 + Django REST Framework 3.16
- **Database**: SQLite 3
- **Machine Learning Pipeline**: `scikit-learn`, `XGBoost`, `SHAP` (Explainable AI), `pandas`, `numpy`, `scipy`, `joblib`
- **Analytics & Visualizations**: `matplotlib`, `seaborn` (Server-side SVG chart generation)
- **Frontend / Styling**: Vanilla CSS design system (`static/css/style.css`), Bootstrap 5 grid utilities, Bootstrap Icons
- **JavaScript**: Vanilla ES6+ JavaScript modules (`static/js/`)

---

## Directory Structure

```text
foster_care_predictor/
├── apps/                        # Modular Django App Subsystems
│   ├── accounts/                # User authentication, RBAC profiles, settings, password management
│   ├── analytics/               # System dashboard, SVG charts, metrics, recent activity
│   ├── api/                     # REST API v1 endpoints, serializers, permissions, API docs
│   ├── children/                # Child welfare profile registry, forms, views
│   ├── core/                    # Landing page, about, contact, synthetic data generation
│   ├── families/                # Foster family registry, capacity checks, profile views
│   ├── placements/              # Placement assignment lifecycle & AJAX summary card API
│   ├── predictions/             # ML prediction inference engine & smart matching API
│   └── reports/                 # Benchmark analytics report library
├── config/                      # Project Settings & Routing
│   ├── settings/                # base.py, development.py, production.py
│   ├── urls.py                  # Root URL dispatcher
│   └── wsgi.py                  # WSGI entry point
├── ml/                          # Machine Learning & Data Pipeline
│   ├── data/                    # Raw & processed synthetic datasets
│   ├── eda/                     # Exploratory Data Analysis scripts
│   ├── features/                # Feature engineering & preprocessors
│   ├── inference/               # ML prediction, SHAP explanation, candidate matching engine
│   ├── models_store/            # Trained model artifacts (.joblib + metadata)
│   └── training/                # Model comparison & training scripts
├── static/                      # Static Web Assets
│   ├── css/style.css            # Master CSS design system (zero inline styles in HTML)
│   └── js/                      # External JS modules (child_form.js, placement_form.js, etc.)
├── templates/                   # Global HTML Templates (base.html, navbar.html, footer.html)
├── manage.py                    # Django CLI entrypoint
└── requirements.txt             # Primary Python dependencies
```

---

## Quick Start & Installation

### 1. Environment Setup
Ensure Python 3.10+ is installed on your system.

```bash
# Clone repository or navigate to root directory
cd foster_care_predictor

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install primary dependencies
pip install -r requirements.txt
```

### 2. Database Migration & Data Ingestion
Initialize database migrations and populate synthetic data for testing:

```bash
# Apply migrations
python manage.py migrate

# Populate synthetic children, families, placements, and predictions
python manage.py generate_synthetic_data

# Train/Verify ML classification models
python manage.py train_models
```

### 3. Create Superuser (Admin)
Create an administrator account to access all features and the Django Admin Panel:

```bash
python manage.py createsuperuser
```

### 4. Run Development Server
Start the Django development web server:

```bash
python manage.py runserver
```

Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## REST API Endpoints (`/api/v1/`)

The application includes a REST API built with Django REST Framework. All endpoints require authentication:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/children/` | List all child records |
| `POST` | `/api/v1/children/` | Register a new child record |
| `GET` | `/api/v1/families/` | List foster family records |
| `POST` | `/api/v1/families/` | Register a new foster family |
| `GET` | `/api/v1/placements/` | List placement records |
| `POST` | `/api/v1/placements/` | Record a new placement |
| `GET` | `/api/v1/predictions/` | List prediction audit logs |
| `POST` | `/api/v1/predictions/` | Run ML compatibility prediction |
| `GET` | `/api/docs/` | Interactive API documentation |

---

## Verification & Testing

To run system checks and automated tests:

```bash
# Run Django system sanity check
python manage.py check

# Run automated test suite
python manage.py test
```

---

## License & Attribution

Developed for child welfare caseworkers, social work researchers, and administrative decision-makers. Built with Python, Django, scikit-learn, and Bootstrap.
