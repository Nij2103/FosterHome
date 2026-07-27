"""
ml.inference.explain

Provides Explainable AI (XAI) for foster care placement compatibility predictions.
Uses SHAP (SHapley Additive exPlanations) or TreeExplainer to calculate local
feature attribution values for a specific prediction instance, answering "WHY did
the model give this compatibility score?".

SURFACES:
1. Top Risk Drivers (+% disruption risk factors)
2. Top Stability Boosters (-% disruption risk / compatibility factors)
3. SHAP Summary Narrative
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Human-readable labels and value formatters for engineered model features
FEATURE_METADATA = {
    "special_needs_mismatch": {
        "label": "Special Needs Mismatch",
        "description": "Child has special needs but family is not accredited for special needs care.",
        "unit": "",
    },
    "cross_state": {
        "label": "Cross-State Placement Barrier",
        "description": "Placement spans across different state jurisdictions.",
        "unit": "",
    },
    "sibling_capacity_fit": {
        "label": "Sibling Group Capacity Fit",
        "description": "Capacity margin remaining for sibling placement.",
        "unit": "slots",
    },
    "occupancy_ratio": {
        "label": "Family Occupancy Load",
        "description": "Ratio of current occupied beds to total licensed home capacity.",
        "unit": "%",
    },
    "experience_years": {
        "label": "Foster Family Experience",
        "description": "Years of active foster parenting experience.",
        "unit": "years",
    },
    "accepts_special_needs": {
        "label": "Special Needs License",
        "description": "Family is certified and willing to support special needs children.",
        "unit": "",
    },
    "accepts_sibling_groups": {
        "label": "Sibling Group License",
        "description": "Family is licensed to accept sibling groups.",
        "unit": "",
    },
    "behavioral_notes_score": {
        "label": "Child Behavioral Support Needs",
        "description": "Assessed behavioral complexity score of the child.",
        "unit": "/10",
    },
    "time_in_care_months": {
        "label": "Time Spent in Care System",
        "description": "Cumulative duration child has been in foster system.",
        "unit": "months",
    },
    "child_age": {
        "label": "Child Age",
        "description": "Age of the child at placement time.",
        "unit": "yrs",
    },
    "capacity": {
        "label": "Licensed Home Capacity",
        "description": "Maximum number of children home is licensed for.",
        "unit": "beds",
    },
    "sibling_group_size": {
        "label": "Sibling Group Size",
        "description": "Number of siblings placed together.",
        "unit": "children",
    },
}


def _format_observed_value(feature_name: str, raw_features: pd.DataFrame) -> str:
    """Extracts human-friendly string for the feature's observed value."""
    if raw_features is None or feature_name not in raw_features.columns:
        return "N/A"
    
    val = raw_features[feature_name].iloc[0]
    
    if feature_name == "special_needs_mismatch":
        return "Yes (Mismatch)" if bool(val) else "No (Matched)"
    elif feature_name == "cross_state":
        return "Yes (Cross-State)" if bool(val) else "No (Same State)"
    elif feature_name in ("special_needs", "accepts_special_needs", "accepts_sibling_groups"):
        return "Yes" if bool(val) else "No"
    elif feature_name == "occupancy_ratio":
        return f"{float(val)*100:.0f}%"
    elif isinstance(val, (int, np.integer)):
        return str(val)
    elif isinstance(val, (float, np.floating)):
        return f"{val:.1f}"
    return str(val)


def compute_prediction_explanation(
    model,
    X_sample: pd.DataFrame,
    feature_columns: list[str],
    raw_features: pd.DataFrame = None,
    disruption_prob: float = 0.5,
) -> dict:
    """
    Computes SHAP values or feature attributions for a single prediction row `X_sample`.

    Returns a structured dictionary:
    {
        "base_value": float,
        "disruption_risk": float,
        "risk_drivers": [...],
        "stability_drivers": [...],
        "shap_summary_text": str,
    }
    """
    shap_values_raw = None
    base_val = 0.35  # Expected baseline disruption rate

    try:
        import shap
        # Try TreeExplainer for decision trees / Random Forest / XGBoost / GradientBoosting
        if hasattr(model, "estimators_") or "Tree" in type(model).__name__ or "Forest" in type(model).__name__ or "XGB" in type(model).__name__ or "GradientBoosting" in type(model).__name__:
            explainer = shap.TreeExplainer(model)
            sv = explainer(X_sample)
            
            # Extract values for class 1 (disruption risk)
            if len(sv.values.shape) == 3:  # (samples, features, classes)
                shap_values_raw = sv.values[0, :, 1]
                if hasattr(explainer, "expected_value") and isinstance(explainer.expected_value, (list, np.ndarray)):
                    base_val = float(explainer.expected_value[1])
            else:
                shap_values_raw = sv.values[0]
                if hasattr(explainer, "expected_value"):
                    base_val = float(explainer.expected_value) if not isinstance(explainer.expected_value, (list, np.ndarray)) else float(explainer.expected_value[0])
    except Exception as exc:
        logger.debug("Native SHAP TreeExplainer calculation fallback activated: %s", exc)

    # Fallback local feature attribution computation if SHAP is unavailable or non-tree
    if shap_values_raw is None:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            importances = np.ones(len(feature_columns)) / len(feature_columns)
        
        # Scale importances by normalized sample feature magnitude
        sample_vec = X_sample.iloc[0].values
        shap_values_raw = importances * np.sign(sample_vec) * np.abs(sample_vec)
        # Normalize sum to approximate disruption risk deviation
        total = np.sum(np.abs(shap_values_raw))
        if total > 0:
            dev = disruption_prob - base_val
            shap_values_raw = (shap_values_raw / total) * abs(dev)

    risk_drivers = []
    stability_drivers = []

    for idx, feature_name in enumerate(feature_columns):
        attr_val = float(shap_values_raw[idx])
        pct_impact = attr_val * 100.0
        
        meta = FEATURE_METADATA.get(feature_name, {
            "label": feature_name.replace("_", " ").title(),
            "description": "",
            "unit": "",
        })
        
        obs_str = _format_observed_value(feature_name, raw_features)
        
        item = {
            "feature": feature_name,
            "label": meta["label"],
            "description": meta["description"],
            "observed_value": obs_str,
            "impact_pct": round(pct_impact, 1),
            "impact_direction": "risk_increase" if pct_impact > 0 else "stability_booster",
            "abs_impact": abs(round(pct_impact, 1)),
        }
        
        if pct_impact > 0.5:
            risk_drivers.append(item)
        elif pct_impact < -0.5:
            stability_drivers.append(item)

    # Sort risk drivers by impact descending, stability by protective impact descending
    risk_drivers = sorted(risk_drivers, key=lambda x: x["impact_pct"], reverse=True)
    stability_drivers = sorted(stability_drivers, key=lambda x: x["impact_pct"])  # most negative first

    # Build plain-English casework summary narrative
    top_risk_names = [f"{r['label']} (+{r['impact_pct']:.1f}%)" for r in risk_drivers[:2]]
    top_stab_names = [f"{s['label']} ({s['impact_pct']:.1f}%)" for s in stability_drivers[:2]]

    summary_parts = []
    if top_risk_names:
        summary_parts.append(f"Risk driven mainly by: {', '.join(top_risk_names)}.")
    if top_stab_names:
        summary_parts.append(f"Compensated by: {', '.join(top_stab_names)}.")
    if not summary_parts:
        summary_parts.append("Placement metrics fall within standard balanced baseline thresholds.")

    summary_text = " ".join(summary_parts)

    return {
        "base_value": round(base_val, 4),
        "disruption_risk": round(disruption_prob, 4),
        "risk_drivers": risk_drivers[:5],
        "stability_drivers": stability_drivers[:5],
        "all_attributions": risk_drivers + stability_drivers,
        "shap_summary_text": summary_text,
    }
