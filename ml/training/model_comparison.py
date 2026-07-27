"""
ml.training.model_comparison

Builds a comparison table across all trained classifiers (classical +
deep learning) and selects a "best" model based on evidence — explicitly
NOT just accuracy, since accuracy is misleading on any dataset with class
imbalance (our disrupted/not-disrupted split is roughly 15/85, per Step
7's generated data). F1 score (harmonic mean of precision and recall) is
used as the primary selection metric because it penalizes a model that
just predicts "not disrupted" for everyone — which would score high
accuracy but be useless for the actual goal of flagging at-risk
placements.
"""

from __future__ import annotations

import pandas as pd


def build_comparison_table(classification_results: dict) -> pd.DataFrame:
    """
    classification_results: output of train_classification.train_and_evaluate_all()
    (may also include a "Deep Learning (MLP)" entry merged in by the
    caller). Excludes the "_split" bookkeeping key.
    """
    rows = []
    for name, result in classification_results.items():
        if name == "_split":
            continue
        m = result["metrics"]
        rows.append({
            "model": name,
            "accuracy": round(m["accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "roc_auc": round(m["roc_auc"], 4) if m.get("roc_auc") is not None else None,
            "cv_accuracy_mean": round(m["cv_accuracy_mean"], 4) if m.get("cv_accuracy_mean") is not None else None,
        })
    df = pd.DataFrame(rows).set_index("model")
    return df.sort_values("f1", ascending=False)


def select_best_model(classification_results: dict, comparison_table: pd.DataFrame) -> tuple[str, object]:
    """
    Returns (best_model_name, fitted_model_object). Selection is by F1
    score (see module docstring for why not accuracy) — the model in
    first position of the already-F1-sorted comparison_table.
    """
    best_name = comparison_table.index[0]
    best_model = classification_results[best_name]["model"]
    return best_name, best_model


def build_regression_comparison_table(regression_results: dict) -> pd.DataFrame:
    rows = []
    for name, result in regression_results.items():
        if name == "_split":
            continue
        m = result["metrics"]
        rows.append({
            "model": name,
            "mae": round(m["mae"], 3),
            "rmse": round(m["rmse"], 3),
            "r2": round(m["r2"], 4),
        })
    df = pd.DataFrame(rows).set_index("model")
    # Lower MAE/RMSE is better, higher R2 is better — sort by R2 descending
    # as the primary "goodness of fit" summary metric.
    return df.sort_values("r2", ascending=False)
