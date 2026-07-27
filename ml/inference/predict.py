"""
ml.inference.predict

Loads whichever model Step 9's train_models command decided was best —
either a classical scikit-learn/XGBoost model (ml/models_store/
best_classifier.joblib) or a Keras MLP (best_classifier.keras +
best_classifier_preprocessing.joblib) — and serves a single compatibility
prediction for a given Child/FosterFamily pair. This is the ONLY place
the persisted model artifacts from Step 9 are loaded and used, keeping
prediction-serving logic in one auditable location.
"""

from __future__ import annotations

from pathlib import Path

from ml.features.feature_engineering import build_single_pair_features, transform_classification_features
from ml.inference.explain import compute_prediction_explanation


class ModelNotTrainedError(Exception):
    """Raised when no trained model artifacts exist yet — the caller
    should surface this as 'run train_models first', not a generic 500."""


def _models_dir() -> Path:
    from django.conf import settings
    return Path(settings.ML_MODELS_DIR)


def load_best_model():
    """
    Returns (model, model_name, feature_columns, preprocessing, is_keras).
    Raises ModelNotTrainedError if neither artifact set exists.
    """
    models_dir = _models_dir()
    joblib_path = models_dir / "best_classifier.joblib"
    keras_path = models_dir / "best_classifier.keras"

    if joblib_path.exists():
        import joblib
        bundle = joblib.load(joblib_path)
        return (
            bundle["model"], bundle["model_name"], bundle["feature_columns"],
            bundle["preprocessing"], False,
        )

    if keras_path.exists():
        import joblib
        from tensorflow import keras as tf_keras
        model = tf_keras.models.load_model(keras_path)
        meta = joblib.load(models_dir / "best_classifier_preprocessing.joblib")
        return (
            model, meta["model_name"], meta["feature_columns"],
            meta["preprocessing"], True,
        )

    raise ModelNotTrainedError(
        "No trained model found in ml/models_store/. Run "
        "`python manage.py train_models` first."
    )


def predict_compatibility(child, family) -> dict:
    """
    child, family: Django model instances (apps.children.models.Child,
    apps.families.models.FosterFamily).

    Returns {"compatibility_score": float, "model_name": str,
             "disruption_risk": float} — compatibility_score is
    1 - disruption_probability, so a HIGHER score means a BETTER
    predicted match, which is the intuitive direction for the UI to
    display (see feature_engineering.py docstring for why disruption
    probability is the underlying learned quantity).
    """
    model, model_name, feature_columns, preprocessing, is_keras = load_best_model()

    child_dict = {
        "id": child.id, "age": child.age, "gender": child.gender, "state": child.state,
        "special_needs": child.special_needs, "sibling_group_size": child.sibling_group_size,
        "behavioral_notes_score": child.behavioral_notes_score,
        "time_in_care_months": child.time_in_care_months,
    }
    family_dict = {
        "id": family.id, "state": family.state, "capacity": family.capacity,
        "current_occupancy": family.current_occupancy, "experience_years": family.experience_years,
        "accepts_special_needs": family.accepts_special_needs,
        "accepts_sibling_groups": family.accepts_sibling_groups, "home_type": family.home_type,
    }

    raw_features = build_single_pair_features(child_dict, family_dict)
    X = transform_classification_features(raw_features, preprocessing)
    X = X[feature_columns]  # enforce exact training column order

    if is_keras:
        disruption_prob = float(model.predict(X.values, verbose=0).ravel()[0])
    else:
        disruption_prob = float(model.predict_proba(X)[:, 1][0])

    explanation = compute_prediction_explanation(
        model=model,
        X_sample=X,
        feature_columns=feature_columns,
        raw_features=raw_features,
        disruption_prob=disruption_prob,
    )

    return {
        "compatibility_score": round(1.0 - disruption_prob, 4),
        "disruption_risk": round(disruption_prob, 4),
        "model_name": model_name,
        "explanation": explanation,
    }

