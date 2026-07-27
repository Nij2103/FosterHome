"""
Management command: train_models

The capstone bridge command for the ML milestone — loads data from the
database, engineers features, trains and compares classification models
(including a deep learning MLP), trains regression models, generates
every evaluation chart, writes a markdown report, and persists the best
classification model + its preprocessing artifacts to ml/models_store/
so a future prediction-serving view (Step 10/11) can load it without
retraining.

Run with: python manage.py train_models
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from ml.features.feature_engineering import (
    build_placement_features,
    build_regression_features,
    encode_and_scale_classification_features,
)
from ml.training import model_comparison, train_classification, train_deep_learning, train_regression
from ml.visualization import charts


class Command(BaseCommand):
    help = "Train and compare ML models for placement disruption prediction and time-in-care regression."

    def handle(self, *args, **options):
        charts_dir = Path(settings.MEDIA_ROOT) / "analytics" / "charts"
        models_dir = Path(settings.ML_MODELS_DIR)
        models_dir.mkdir(parents=True, exist_ok=True)
        report_path = Path(settings.BASE_DIR) / "docs" / "ml_report.md"

        children_df = pd.DataFrame(list(Child.objects.values()))
        families_df = pd.DataFrame(list(FosterFamily.objects.values()))
        placements_df = pd.DataFrame(list(Placement.objects.values()))

        if placements_df.empty:
            self.stdout.write(self.style.ERROR(
                "No placement data found. Run `python manage.py generate_synthetic_data` first."
            ))
            return

        report = ["# ML Training Report", ""]

        # ==============================================================
        # CLASSIFICATION: placement disruption prediction
        # ==============================================================
        self.stdout.write("Building classification features...")
        placement_features = build_placement_features(children_df, families_df, placements_df)
        X, y, preprocessing = encode_and_scale_classification_features(placement_features)

        report.append(f"## Classification: Placement Disruption Prediction")
        report.append(f"- Samples: {len(X)}")
        report.append(f"- Class balance: {y.value_counts(normalize=True).round(3).to_dict()}")
        report.append("")

        self.stdout.write("Training classification models (Logistic Regression, Decision Tree, "
                           "Random Forest, Gradient Boosting, SVM, KNN, XGBoost)...")
        clf_results = train_classification.train_and_evaluate_all(X, y)
        split = clf_results.pop("_split")

        # --- Deep learning comparison ---
        n_samples = len(X)
        justified, reason = train_deep_learning.is_deep_learning_justified(n_samples)
        self.stdout.write(f"Deep learning justification check: {reason}")
        report.append(f"### Deep Learning Justification Check\n{reason}\n")

        try:
            self.stdout.write("Training MLP (deep learning comparison model)...")
            mlp_result = train_deep_learning.train_and_evaluate_mlp(
                split["X_train"].values, split["X_test"].values,
                split["y_train"].values, split["y_test"].values,
            )
            clf_results["Deep Learning (MLP)"] = mlp_result
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f"Skipping Deep Learning (MLP): {e}"))
            report.append("### Deep Learning (MLP)\n*Skipped: TensorFlow is not installed in this environment.*\n")

        # --- Hyperparameter tuning demo on Random Forest ---
        self.stdout.write("Running GridSearchCV hyperparameter tuning on Random Forest...")
        best_rf, best_params, best_cv_score = train_classification.tune_random_forest(
            split["X_train"], split["y_train"],
        )
        report.append(f"### Random Forest Hyperparameter Tuning (GridSearchCV, 5-fold, scoring=f1)")
        report.append(f"- Best params: `{best_params}`")
        report.append(f"- Best CV F1: {best_cv_score:.4f}\n")

        # --- Comparison table + best model selection ---
        comparison_table = model_comparison.build_comparison_table(clf_results)
        best_name, best_model = model_comparison.select_best_model(clf_results, comparison_table)
        report.append("### Model Comparison (sorted by F1 score)")
        report.append(comparison_table.to_markdown())
        report.append(f"\n**Selected model: {best_name}** (highest F1 — chosen over raw accuracy "
                       f"because the disruption class is a minority class; accuracy alone would "
                       f"favor a model that just predicts 'not disrupted' for everyone).\n")

        # Honest, dynamic commentary on the DL-vs-classical outcome —
        # written to reflect what actually happened this run rather than
        # leaving the earlier justification-check text's expectation
        # unaddressed either way.
        test_set_size = len(split["y_test"])
        if "Deep Learning (MLP)" in comparison_table.index:
            if best_name == "Deep Learning (MLP)":
                classical_scores = comparison_table.drop(index="Deep Learning (MLP)")["f1"]
                runner_up_name = classical_scores.idxmax()
                runner_up_f1 = classical_scores.max()
                mlp_f1 = comparison_table.loc["Deep Learning (MLP)", "f1"]
                report.append(
                    f"**Note on the deep learning result**: the MLP narrowly outperformed the best "
                    f"classical model ({runner_up_name}, F1={runner_up_f1}) this run (F1={mlp_f1}). "
                    f"With only {test_set_size} test samples, a single additional correct prediction "
                    f"shifts F1 by roughly {round(1/test_set_size, 3)} — a margin this small should be "
                    f"read as 'roughly tied with the best classical models,' not as deep learning "
                    f"decisively winning. The dataset-size caveat from the justification check above "
                    f"still applies: this result would need a much larger test set before concluding "
                    f"the MLP is genuinely the better choice for this problem.\n"
                )
            else:
                mlp_f1 = comparison_table.loc["Deep Learning (MLP)", "f1"]
                best_f1 = comparison_table.loc[best_name, "f1"]
                report.append(
                    f"**Note on the deep learning result**: the MLP (F1={mlp_f1}) did not outperform "
                    f"the selected classical model ({best_name}, F1={best_f1}) — consistent with the "
                    f"dataset-size expectation noted in the justification check above.\n"
                )
        else:
            report.append("**Note on deep learning**: MLP training was skipped because TensorFlow is not installed in this environment.\n")

        # ==============================================================
        # Charts: classification evaluation
        # ==============================================================
        self.stdout.write("Generating classification evaluation charts...")
        chart_paths = []

        for name in ["Logistic Regression", "Random Forest", best_name]:
            if name in clf_results:
                cm = clf_results[name]["metrics"]["confusion_matrix"]
                chart_paths.append(charts.plot_confusion_matrix(
                    cm, ["Not Disrupted", "Disrupted"], name,
                    charts_dir / f"confusion_matrix_{name.replace(' ', '_').replace('(', '').replace(')', '')}.png",
                ))

        roc_eligible = {k: v for k, v in clf_results.items() if v.get("y_proba") is not None}
        chart_paths.append(charts.plot_roc_curves(roc_eligible, charts_dir / "roc_curves_comparison.png"))
        chart_paths.append(charts.plot_precision_recall_curves(roc_eligible, charts_dir / "precision_recall_curves.png"))

        if hasattr(best_model, "feature_importances_"):
            importances = pd.Series(best_model.feature_importances_, index=X.columns)
            chart_paths.append(charts.plot_feature_importance(
                importances, best_name, charts_dir / "feature_importance.png",
            ))

        chart_paths.append(charts.plot_model_metric_comparison(
            comparison_table, "accuracy", charts_dir / "model_comparison_accuracy.png",
        ))
        chart_paths.append(charts.plot_model_metric_comparison(
            comparison_table, "f1", charts_dir / "model_comparison_f1.png",
        ))

        # ==============================================================
        # REGRESSION: time-in-care prediction
        # ==============================================================
        self.stdout.write("Training regression models (time_in_care_months)...")
        X_reg, y_reg = build_regression_features(children_df)
        reg_results = train_regression.train_and_evaluate_regressors(X_reg, y_reg)
        reg_split = reg_results.pop("_split")

        reg_comparison = model_comparison.build_regression_comparison_table(reg_results)
        report.append("## Regression: Time-in-Care Prediction (months)")
        report.append(reg_comparison.to_markdown())
        report.append("")

        best_reg_name = reg_comparison.index[0]
        chart_paths.append(charts.plot_regression_predicted_vs_actual(
            reg_results[best_reg_name]["y_test"], reg_results[best_reg_name]["y_pred"],
            best_reg_name, charts_dir / "regression_predicted_vs_actual.png",
        ))

        for path in chart_paths:
            self.stdout.write(f"  saved {path}")

        # ==============================================================
        # Persist best model + preprocessing artifacts
        # ==============================================================
        # Clear any stale artifacts from a previous run first — if the
        # best model type changes between runs (e.g. XGBoost this run,
        # MLP next run), leaving old files behind would create ambiguity
        # about which one is actually current.
        for stale in models_dir.glob("best_classifier*"):
            stale.unlink()

        is_keras_model = best_name == "Deep Learning (MLP)"

        if is_keras_model:
            # joblib/pickle is the wrong tool for a TensorFlow/Keras
            # model — its native .keras format is what TensorFlow itself
            # documents and guarantees round-trips correctly.
            model_path = models_dir / "best_classifier.keras"
            best_model.save(model_path)
            preprocessing_path = models_dir / "best_classifier_preprocessing.joblib"
            joblib.dump({
                "model_name": best_name,
                "feature_columns": list(X.columns),
                "preprocessing": preprocessing,
            }, preprocessing_path)
        else:
            model_path = models_dir / "best_classifier.joblib"
            joblib.dump({
                "model": best_model,
                "model_name": best_name,
                "feature_columns": list(X.columns),
                "preprocessing": preprocessing,
            }, model_path)

        metadata = {
            "model_name": best_name,
            "metrics": comparison_table.loc[best_name].to_dict(),
            "trained_on_n_samples": len(X),
            "feature_columns": list(X.columns),
        }
        (models_dir / "best_classifier_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(str(line) for line in report))

        self.stdout.write(self.style.SUCCESS(
            f"Best model ({best_name}) saved to {model_path}. Report written to {report_path}."
        ))
