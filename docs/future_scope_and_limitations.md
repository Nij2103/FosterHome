# Future Scope & Limitations

Stated together and honestly, because a limitation you've clearly
identified is a much stronger position (in a viva or a report) than one
an examiner finds for you.

## Limitations (current state)

- **Small dataset for the deep learning comparison.** ~900 synthetic
  children / ~380 placements is enough to demonstrate the ML pipeline
  end-to-end, but the deep learning justification check itself
  recommends ~1000+ samples before an MLP has a genuine advantage over
  classical models. The current result (MLP narrowly ahead) is honestly
  flagged in `docs/ml_report.md` as within statistical noise given the
  test-set size.
- **Synchronous scraping and training.** `scrape_reports` and
  `train_models` both run in-process (a management command, or a
  request/response cycle for the Admin-triggered re-scrape). Fine at
  this scale; would need a task queue (Celery/Django-RQ) for a real
  multi-user deployment — documented in `docs/deployment_guide.md`.
- **SQLite, not a concurrent-write-optimized database.** Appropriate for
  single-evaluator/local use; Postgres would be needed for real
  multi-user concurrent access.
- **KNN has no direct class-weighting mechanism.** Unlike the other
  classifiers, KNN couldn't be rebalanced for the disruption class
  imbalance the same way — noted explicitly in
  `ml/training/train_classification.py` rather than silently accepted.
- **National-only AFCARS statistics in the bundled fixture.** State-level
  breakdowns exist in AFCARS's real published data but weren't ingested
  — the `ReportStatistic.state` field currently only holds `"National"`
  for the scraped rows (synthetic `Child`/`FosterFamily` records do have
  per-record states, generated independently).
- **No real-time re-scraping in this sandboxed environment.** The
  network this project was built in only allows a small domain
  allowlist; the live AFCARS scraping path is written and would work
  wherever normal internet access is available, but was only
  demonstrated here against a local fixture mirroring the real site's
  structure.
- **GridSearchCV tuning is demonstrated on one model** (Random Forest),
  not all seven classifiers — an intentional scope choice (exhaustive
  tuning across all models would cost far more runtime than the teaching
  value justifies at this dataset size), not an oversight.

## Future scope

- **Task queue integration** (Celery + Redis or Django-RQ) for the
  scraper and model training, enabling scheduled re-scraping and
  retraining without blocking a web worker.
- **State-level AFCARS ingestion**, enabling genuine state-wise
  comparison charts using real (not synthetic) data.
- **SMOTE or similar resampling** as an alternative/complement to
  `class_weight` balancing for the disruption classification target.
- **A larger, still-synthetic dataset** (several thousand records) to
  properly test whether deep learning provides a real advantage at
  scale, resolving the current "roughly tied" finding one way or the
  other.
- **Model versioning and A/B comparison in production** — currently
  `train_models` overwrites the single "best" model artifact each run;
  a real deployment would keep a model registry with version history and
  the ability to roll back.
- **Audit logging for predictions** — currently a `Prediction` row
  records who requested it and when, but a full casework audit trail
  (e.g. linking which specific predictions informed which final
  `Placement` decision) would need an explicit link field.
- **Notification system** — e.g. alerting a case worker when a family's
  `current_occupancy` frees up and matches a waiting child's profile,
  rather than requiring someone to check manually.
- **Multi-factor authentication for Admin accounts**, given the
  elevated privileges (user role management, model retraining, report
  re-scraping).
- **Internationalization** — the project currently assumes U.S. states
  and English; `USE_I18N = True` is already set in Django settings as a
  starting point.
