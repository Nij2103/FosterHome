"""
ml.training.train_classification

Trains and evaluates multiple classifiers on the placement-disruption
target (see feature_engineering.py docstring for why this framing is
used instead of an invented "compatibility score"). Every model uses the
SAME train/test split for a fair comparison, k-fold cross-validation on
the training set, and one model (Random Forest — the strongest baseline
in initial testing) gets a light hyperparameter search via GridSearchCV
to demonstrate the technique without an excessive runtime cost for a
dataset this size.

WHY THESE SPECIFIC MODELS:
Logistic Regression (linear baseline, interpretable coefficients),
Decision Tree (interpretable, no scaling needed, prone to overfitting —
good teaching contrast with Random Forest), Random Forest (ensemble,
usually strong on tabular data, gives feature importances), Gradient
Boosting (sequential ensemble, often outperforms Random Forest on
structured data), SVM (margin-based, benefits from our StandardScaler
step), K-Nearest Neighbors (instance-based, distance-sensitive — again
benefits from scaling), and XGBoost (industry-standard gradient boosting
implementation, included since it's available and commonly expected in a
final-year ML comparison chapter).
"""

from __future__ import annotations

import numpy as np
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

RANDOM_STATE = 42


def get_candidate_models(scale_pos_weight: float = 1.0) -> dict:
    """
    Returns a fresh dict of {name: unfitted estimator} every call — models
    are stateful once fit, so callers must not reuse a shared instance
    across multiple fit() calls (e.g. across cross-validation folds run
    manually rather than via cross_val_score).

    WHY class_weight="balanced" ON SEVERAL MODELS:
    Our disruption target is imbalanced (~86% not-disrupted / 14%
    disrupted, per the Step 7 synthetic generator). Without correction, a
    classifier can score high accuracy by simply never predicting the
    minority class — this actually happened during development: SVM and
    KNN both scored precision=recall=F1=0.0 on the disrupted class before
    this fix, meaning they were useless for the project's actual goal
    despite ~87% "accuracy". class_weight="balanced" (supported by
    Logistic Regression, Decision Tree, Random Forest, and SVM) rescales
    the loss to penalize minority-class errors more heavily.
    XGBoost uses its own `scale_pos_weight` parameter for the same
    purpose (ratio of negative to positive samples in the training set).
    KNN has no direct class-weighting mechanism — noted as a known
    limitation of that algorithm on imbalanced data, not silently ignored.
    """
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced",
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=6, random_state=RANDOM_STATE, class_weight="balanced",
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=RANDOM_STATE, class_weight="balanced",
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
        # sklearn's GradientBoostingClassifier has no class_weight param —
        # a known asymmetry with RandomForest, documented rather than worked
        # around with a hack (e.g. manual sample_weight is possible but
        # adds complexity out of proportion to this project's scope).
        "SVM (RBF kernel)": SVC(
            probability=True, random_state=RANDOM_STATE, class_weight="balanced",
        ),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=7, weights="distance"),
        # weights="distance" is KNN's closest available lever here — it
        # doesn't rebalance classes, but it does reduce the influence of
        # distant majority-class neighbors, which helps somewhat.
        "XGBoost": XGBClassifier(
            eval_metric="logloss", random_state=RANDOM_STATE, verbosity=0,
            scale_pos_weight=scale_pos_weight,
        ),
    }


def train_and_evaluate_all(X, y, test_size: float = 0.2) -> dict:
    """
    Trains every candidate model on the same split, evaluates on the held
    -out test set, and 5-fold cross-validates on the training set (for a
    variance-aware accuracy estimate, not just a single train/test number).

    Returns {model_name: {"model": fitted_estimator, "metrics": {...},
                           "y_test": ..., "y_pred": ..., "y_proba": ...}}
    plus a special "_split" key holding the raw train/test arrays, so the
    caller (management command) can reuse the exact same split for
    plotting without recomputing it.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results = {}

    # Ratio of negative to positive samples in the training set — the
    # standard formula for XGBoost's scale_pos_weight on imbalanced data.
    n_negative = (y_train == 0).sum()
    n_positive = (y_train == 1).sum()
    scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1.0

    for name, model in get_candidate_models(scale_pos_weight=scale_pos_weight).items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

        cv_scores = cross_val_score(clone(model), X_train, y_train, cv=cv, scoring="accuracy")

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_proba) if y_proba is not None else None,
            "cv_accuracy_mean": cv_scores.mean(),
            "cv_accuracy_std": cv_scores.std(),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }

        results[name] = {
            "model": model,
            "metrics": metrics,
            "y_test": y_test,
            "y_pred": y_pred,
            "y_proba": y_proba,
        }

    results["_split"] = {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test}
    return results


def tune_random_forest(X_train, y_train) -> RandomForestClassifier:
    """
    Light GridSearchCV over Random Forest hyperparameters — demonstrates
    the tuning technique the syllabus asks for without an excessive
    search space (an exhaustive grid over 7 models would cost far more
    runtime than the teaching value justifies for a dataset this size).
    Random Forest was chosen for tuning because it was the strongest or
    near-strongest baseline in initial evaluation and exposes intuitive,
    well-understood hyperparameters.
    """
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [4, 6, 8, None],
        "min_samples_split": [2, 5, 10],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE, class_weight="balanced"),
        param_grid, cv=cv, scoring="f1", n_jobs=-1,
    )
    search.fit(X_train, y_train)
    return search.best_estimator_, search.best_params_, search.best_score_
