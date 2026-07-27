"""
ml.visualization.charts

Seaborn-primary, Matplotlib-supporting chart generators (per the project
brief's stated preference). Every function takes a pandas DataFrame plus
an output path, saves a PNG, and returns the path — this consistent
signature is what lets the (future) Django dashboard view just call these
functions and hand the returned paths to a template's <img> tags, rather
than each chart needing bespoke wiring.

CHARTS BUILT HERE (exploratory/descriptive — don't require a trained
model): missing-values bar chart, age histogram, gender count plot,
state-wise bar chart, correlation heatmap, outlier box plot, violin plot,
pair plot, placement-status count plot, year-wise trend line chart
(sourced from the Step 6 scraper's real AFCARS ReportStatistic data),
and a regression/scatter plot.

CHARTS DEFERRED TO ml/training/ (Step 9): confusion matrix, ROC curve,
precision-recall curve, feature importance, accuracy/F1 model comparison
— these all require a trained model's predictions to exist, so building
them now would mean plotting nothing meaningful. Building placeholder
charts just to tick a box would be worse than being upfront that they
belong to the next milestone.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — required for server-side chart generation
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# matplotlib logs routine internal messages (e.g. category-axis unit
# conversion) at INFO level. Our project's dev logging config runs at
# INFO for readability of OUR code's logs — without this, matplotlib's
# internal chatter leaks into every chart-generating command's output.
logging.getLogger("matplotlib").setLevel(logging.WARNING)

# Light, professional palette consistent with the Django UI theme
# (see static/css/theme.css) — sky blue / light green / pastel orange.
THEME_PALETTE = ["#3a7ca5", "#7fb069", "#e8a87c", "#c1666b", "#8e7dbe"]
sns.set_theme(style="whitegrid", palette=THEME_PALETTE)
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"


def _save_fig(fig, output_path: str | Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)


# ---------------------------------------------------------------------
# Missing values / data quality
# ---------------------------------------------------------------------
def plot_missing_values(missing_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    if missing_df.empty:
        ax.text(0.5, 0.5, "No missing values detected", ha="center", va="center", fontsize=12)
        ax.axis("off")
    else:
        sns.barplot(data=missing_df, x="missing_pct", y="column", ax=ax, color=THEME_PALETTE[3])
        ax.set_xlabel("Missing (%)")
        ax.set_ylabel("")
    ax.set_title("Missing Values by Column")
    return _save_fig(fig, output_path)


# ---------------------------------------------------------------------
# Children distributions
# ---------------------------------------------------------------------
def plot_age_distribution(children_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(data=children_df, x="age", bins=18, kde=True, ax=ax, color=THEME_PALETTE[0])
    ax.set_title("Age Distribution of Children in Care")
    ax.set_xlabel("Age (years)")
    return _save_fig(fig, output_path)


def plot_gender_distribution(children_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.countplot(data=children_df, x="gender", ax=ax, hue="gender", legend=False)
    ax.set_title("Gender Distribution")
    return _save_fig(fig, output_path)


def plot_state_wise_children(children_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    order = children_df["state"].value_counts().index
    sns.countplot(data=children_df, y="state", order=order, ax=ax, color=THEME_PALETTE[1])
    ax.set_title("Children in Care by State")
    ax.set_xlabel("Count")
    ax.set_ylabel("")
    return _save_fig(fig, output_path)


def plot_special_needs_by_placement(children_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=children_df, x="special_needs", hue="is_placed", ax=ax)
    ax.set_title("Placement Status by Special Needs")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["No special needs", "Special needs"])
    ax.legend(title="Placed?", labels=["No", "Yes"])
    return _save_fig(fig, output_path)


# ---------------------------------------------------------------------
# Correlation / outliers / distribution shape
# ---------------------------------------------------------------------
def plot_correlation_heatmap(corr_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, square=True)
    ax.set_title("Correlation Matrix (Children — Numeric Features)")
    return _save_fig(fig, output_path)


def plot_outlier_boxplot(df: pd.DataFrame, column: str, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(data=df, x=column, ax=ax, color=THEME_PALETTE[2])
    ax.set_title(f"Outlier Detection (IQR method): {column}")
    return _save_fig(fig, output_path)


def plot_violin_behavioral_score(children_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.violinplot(data=children_df, x="special_needs", y="behavioral_notes_score", ax=ax, hue="special_needs", legend=False)
    ax.set_title("Behavioral Notes Score by Special Needs Status")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["No special needs", "Special needs"])
    return _save_fig(fig, output_path)


def plot_pairplot(children_df: pd.DataFrame, columns: list[str], output_path: str | Path) -> str:
    """
    Seaborn's pairplot manages its own Figure internally (via a
    PairGrid), so it doesn't go through the shared _save_fig() helper —
    handled directly here instead.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grid = sns.pairplot(children_df[columns + ["special_needs"]], hue="special_needs", palette=THEME_PALETTE[:2])
    grid.figure.suptitle("Pairwise Relationships — Numeric Features", y=1.02)
    grid.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(grid.figure)
    return str(output_path)


# ---------------------------------------------------------------------
# Foster families
# ---------------------------------------------------------------------
def plot_family_capacity_distribution(families_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    # Cast to string explicitly: passing a numeric dtype straight into a
    # categorical countplot leaves matplotlib guessing whether the axis
    # is numeric or categorical, which raises a "categorical units"
    # warning even though the plot renders correctly either way — casting
    # removes the ambiguity rather than just living with the warning.
    plot_df = families_df.copy()
    plot_df["capacity"] = plot_df["capacity"].astype(str)
    order = sorted(plot_df["capacity"].unique(), key=int)
    sns.countplot(data=plot_df, x="capacity", order=order, ax=ax, color=THEME_PALETTE[4])
    ax.set_title("Foster Family Capacity Distribution")
    return _save_fig(fig, output_path)


def plot_home_type_distribution(families_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.countplot(data=families_df, x="home_type", ax=ax, hue="home_type", legend=False)
    ax.set_title("Foster Family Home Type")
    return _save_fig(fig, output_path)


# ---------------------------------------------------------------------
# Placements
# ---------------------------------------------------------------------
def plot_placement_status_counts(placements_df: pd.DataFrame, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    order = placements_df["status"].value_counts().index
    sns.countplot(data=placements_df, x="status", order=order, ax=ax, hue="status", legend=False)
    ax.set_title("Placement Outcomes")
    return _save_fig(fig, output_path)


def plot_experience_vs_disruption(placements_df: pd.DataFrame, output_path: str | Path) -> str:
    """
    Regression plot of family experience_years vs. disruption (0/1) —
    a logistic-style regplot since the target is binary.
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    plot_df = placements_df.copy()
    plot_df["disrupted"] = (plot_df["status"] == "disrupted").astype(int)
    sns.regplot(
        data=plot_df, x="experience_years", y="disrupted", ax=ax,
        logistic=True, y_jitter=0.03, scatter_kws={"alpha": 0.4, "s": 20},
        line_kws={"color": THEME_PALETTE[3]},
    )
    ax.set_title("Family Experience vs. Placement Disruption Probability")
    ax.set_ylabel("Disrupted (0/1, jittered)")
    return _save_fig(fig, output_path)


# ---------------------------------------------------------------------
# Scraped government report data (Step 6 integration)
# ---------------------------------------------------------------------
def plot_year_wise_trend(stats_df: pd.DataFrame, metric_name: str, output_path: str | Path) -> str:
    """
    Line chart of a single metric over time, sourced from the REAL
    scraped ReportStatistic data (Step 6) — e.g. national foster care
    entries/exits by fiscal year from the actual AFCARS report.
    """
    fig, ax = plt.subplots(figsize=(7, 4))
    subset = stats_df[stats_df["metric_name"] == metric_name].sort_values("year")
    sns.lineplot(data=subset, x="year", y="value", marker="o", ax=ax, color=THEME_PALETTE[0])
    ax.set_title(f"Year-wise Trend: {metric_name.replace('_', ' ').title()}")
    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("Count")
    return _save_fig(fig, output_path)


# ---------------------------------------------------------------------
# Model evaluation charts (Step 9 — require a trained model's actual
# predictions, which is why these were deliberately NOT built in Step 8)
# ---------------------------------------------------------------------
def plot_confusion_matrix(cm, labels: list[str], model_name: str, output_path: str | Path) -> str:
    import numpy as np
    fig, ax = plt.subplots(figsize=(5, 4.5))
    cm_arr = np.array(cm)
    sns.heatmap(cm_arr, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax, cbar=False)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix — {model_name}")
    return _save_fig(fig, output_path)


def plot_roc_curves(model_results: dict, output_path: str | Path) -> str:
    """
    model_results: {model_name: {"y_test": ..., "y_proba": ...}, ...}
    Plots every model's ROC curve on one axes for direct visual comparison
    — this is the standard way to compare classifiers' discrimination
    ability across all thresholds, not just the default 0.5 cutoff.
    """
    from sklearn.metrics import roc_curve, auc

    fig, ax = plt.subplots(figsize=(7, 6))
    for idx, (name, result) in enumerate(model_results.items()):
        if result.get("y_proba") is None:
            continue
        fpr, tpr, _ = roc_curve(result["y_test"], result["y_proba"])
        roc_auc = auc(fpr, tpr)
        color = THEME_PALETTE[idx % len(THEME_PALETTE)]
        ax.plot(fpr, tpr, label=f"{name} (AUC={roc_auc:.3f})", color=color)

    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random baseline")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curves — Model Comparison")
    ax.legend(loc="lower right", fontsize=8)
    return _save_fig(fig, output_path)


def plot_precision_recall_curves(model_results: dict, output_path: str | Path) -> str:
    from sklearn.metrics import precision_recall_curve

    fig, ax = plt.subplots(figsize=(7, 6))
    for idx, (name, result) in enumerate(model_results.items()):
        if result.get("y_proba") is None:
            continue
        precision, recall, _ = precision_recall_curve(result["y_test"], result["y_proba"])
        color = THEME_PALETTE[idx % len(THEME_PALETTE)]
        ax.plot(recall, precision, label=name, color=color)

    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curves — Model Comparison")
    ax.legend(loc="lower left", fontsize=8)
    return _save_fig(fig, output_path)


def plot_feature_importance(importances: pd.Series, model_name: str, output_path: str | Path, top_n: int = 15) -> str:
    fig, ax = plt.subplots(figsize=(7, 5))
    top = importances.sort_values(ascending=False).head(top_n)
    sns.barplot(x=top.values, y=top.index, ax=ax, color=THEME_PALETTE[0])
    ax.set_title(f"Feature Importance — {model_name}")
    ax.set_xlabel("Importance")
    ax.set_ylabel("")
    return _save_fig(fig, output_path)


def plot_model_metric_comparison(metrics_df: pd.DataFrame, metric: str, output_path: str | Path) -> str:
    """
    metrics_df: rows=model names, columns include the requested metric
    (e.g. 'accuracy', 'f1'). Produces a horizontal bar chart ranking every
    model by that metric — used for both the accuracy comparison and F1
    comparison charts requested in the project brief (same function,
    different `metric` argument, rather than near-duplicate functions).
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ordered = metrics_df.sort_values(metric, ascending=True)
    sns.barplot(data=ordered, x=metric, y=ordered.index, ax=ax, color=THEME_PALETTE[1])
    ax.set_title(f"Model Comparison — {metric.replace('_', ' ').title()}")
    ax.set_xlabel(metric.replace("_", " ").title())
    ax.set_ylabel("")
    return _save_fig(fig, output_path)


def plot_regression_predicted_vs_actual(y_test, y_pred, model_name: str, output_path: str | Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_test, y_pred, alpha=0.4, color=THEME_PALETTE[0], s=20)
    lims = [min(min(y_test), min(y_pred)), max(max(y_test), max(y_pred))]
    ax.plot(lims, lims, linestyle="--", color=THEME_PALETTE[3], label="Perfect prediction")
    ax.set_xlabel("Actual time_in_care_months")
    ax.set_ylabel("Predicted time_in_care_months")
    ax.set_title(f"Predicted vs. Actual — {model_name}")
    ax.legend()
    return _save_fig(fig, output_path)
