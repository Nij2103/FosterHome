"""
ml.eda.eda_report

Standard exploratory data analysis utilities, applied to the Child and
FosterFamily datasets. Kept as small, single-purpose, composable functions
(rather than one monolithic "run everything" function) so each can be
unit-tested and reused independently — e.g. the ML pipeline's feature
engineering step (Step 9) reuses `numeric_columns()` and
`detect_outliers_iqr()` rather than duplicating that logic.

Every function takes and returns plain pandas objects — no Django imports
here, consistent with the ml/ package's framework-independence principle
(Step 2 design notes).
"""

from __future__ import annotations

import pandas as pd


def missing_values_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: column, missing_count, missing_pct —
    sorted descending by missing_pct. An empty result (0 rows) means no
    missing values were found, which is itself a useful EDA finding to
    report, not an error.
    """
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df) * 100).round(2)
    summary = pd.DataFrame({
        "column": missing_count.index,
        "missing_count": missing_count.values,
        "missing_pct": missing_pct.values,
    })
    summary = summary[summary["missing_count"] > 0].sort_values("missing_pct", ascending=False)
    return summary.reset_index(drop=True)


def duplicate_rows_summary(df: pd.DataFrame, subset: list[str] | None = None) -> dict:
    """
    Returns {"duplicate_count": int, "duplicate_pct": float}.
    `subset` lets the caller check duplicates on a meaningful business key
    (e.g. same child appearing twice) rather than exact full-row duplicates,
    which are rare by construction once a surrogate primary key exists.
    """
    duplicate_count = int(df.duplicated(subset=subset).sum())
    duplicate_pct = round(duplicate_count / len(df) * 100, 2) if len(df) else 0.0
    return {"duplicate_count": duplicate_count, "duplicate_pct": duplicate_pct}


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def distribution_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wraps pandas' .describe() for numeric columns — count, mean, std,
    min, quartiles, max — the standard first-look statistics table.
    """
    cols = numeric_columns(df)
    return df[cols].describe().transpose().round(2)


def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Standard IQR (interquartile range) outlier detection: a value is
    flagged if it falls below Q1 - 1.5*IQR or above Q3 + 1.5*IQR. This is
    the conventional, explainable method taught alongside pandas EDA
    (versus a z-score method, which assumes roughly-normal data — several
    of our fields, like time_in_care_months, are deliberately
    right-skewed by design, per the synthetic generator's exponential
    distribution, so IQR is the more appropriate/defensible choice here).
    """
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return df[(df[column] < lower_bound) | (df[column] > upper_bound)]


def outlier_summary(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """
    Runs detect_outliers_iqr() across multiple numeric columns at once,
    returning a summary table: column, outlier_count, outlier_pct,
    lower_bound, upper_bound.
    """
    cols = columns or numeric_columns(df)
    rows = []
    for col in cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        rows.append({
            "column": col,
            "outlier_count": len(outliers),
            "outlier_pct": round(len(outliers) / len(df) * 100, 2) if len(df) else 0.0,
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
        })
    return pd.DataFrame(rows).sort_values("outlier_pct", ascending=False).reset_index(drop=True)


def correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """
    Numeric-only correlation matrix. Pearson (linear correlation) is the
    default per standard EDA practice; Spearman is offered as an option
    for monotonic-but-nonlinear relationships (e.g. time_in_care_months,
    which is exponentially distributed by construction).
    """
    cols = numeric_columns(df)
    return df[cols].corr(method=method).round(3)
