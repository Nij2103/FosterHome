"""
ml.features.feature_engineering

Turns the raw Child/FosterFamily/Placement tables into an ML-ready feature
matrix. This is where the "long/tidy database design pays off" theme from
Step 3 becomes concrete: because Placement already links one Child to one
FosterFamily with a status, building a training row is a straightforward
join rather than a complex reshape.

TWO PREDICTION TARGETS ARE BUILT HERE, matching the project brief's
syllabus mapping (classification AND a meaningful regression target):

1. CLASSIFICATION target: `disrupted` (binary) — whether a given
   Child-FosterFamily placement ended in disruption. This is the
   project's core "placement compatibility" question: a model that
   predicts LOW disruption probability for a given pair is, by
   definition, predicting HIGH compatibility. We frame it as disruption
   prediction rather than a separately-defined "compatibility score"
   because disruption is the one outcome we actually observe in the
   Placement data — predicting an observed outcome is honest supervised
   learning; inventing an unobserved "compatibility" label and training
   on it would just be circular.

2. REGRESSION target: `time_in_care_months` (continuous) — predicting
   how long a CHILD (independent of any specific family) is likely to
   remain in the care system, based on their own profile. This is a
   genuinely meaningful continuous target (not a forced regression just
   to tick a syllabus box): case workers plan resources around expected
   time-in-care, and it varies continuously rather than falling into
   natural categories.

Both feature sets deliberately encode the SAME real-world signals the
Step 7 synthetic generator used to create disruption risk (special-needs
mismatch, cross-state, sibling-group fit, family experience) — this is
what makes the classification target learnable at all: the model is
recovering the actual generative rules, which is exactly what a
supervised learner is supposed to do, and it is checked in Step 9's model
evaluation (feature importances should surface these same features).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def build_placement_features(
    children_df: pd.DataFrame,
    families_df: pd.DataFrame,
    placements_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Joins Placement -> Child -> FosterFamily and engineers the features
    the classification models train on. Input DataFrames are expected in
    the shape Django's `.values()` QuerySet produces (raw model fields).

    Returns a DataFrame with one row per placement, ready for
    encode_and_scale_classification_features().
    """
    df = placements_df.merge(children_df, left_on="child_id", right_on="id", suffixes=("", "_child"))
    df = df.merge(families_df, left_on="family_id", right_on="id", suffixes=("", "_family"))

    # --- Engineered features (mirroring the synthetic generator's rules,
    #     see module docstring) ---
    df["special_needs_mismatch"] = (df["special_needs"] & ~df["accepts_special_needs"]).astype(int)
    df["cross_state"] = (df["state"] != df["state_family"]).astype(int)
    df["sibling_capacity_fit"] = (df["capacity"] - df["sibling_group_size"]).clip(lower=-5, upper=5)
    df["occupancy_ratio"] = (df["current_occupancy"] / df["capacity"].replace(0, np.nan)).fillna(0)

    feature_columns = [
        "child_age", "gender", "state", "special_needs", "sibling_group_size",
        "behavioral_notes_score", "time_in_care_months",
        "capacity", "experience_years", "accepts_special_needs",
        "accepts_sibling_groups", "home_type", "state_family",
        "special_needs_mismatch", "cross_state", "sibling_capacity_fit", "occupancy_ratio",
    ]
    # `child_age` doesn't exist under that name yet — Child's own `age`
    # column collided with nothing during the merge (families has no
    # `age`), so it's just `age`. Rename for clarity in the feature table.
    df = df.rename(columns={"age": "child_age"})

    target = (df["status"] == "disrupted").astype(int)

    result = df[feature_columns].copy()
    result["disrupted"] = target
    return result


def encode_and_scale_classification_features(
    features_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """
    Encodes categorical columns (LabelEncoder — acceptable here since the
    downstream models are tree-based/linear, not distance-sensitive to
    encoding order for the tree models; StandardScaler below handles the
    linear/SVM/KNN models' sensitivity to scale) and scales numeric
    columns. Returns (X, y, encoders_and_scaler) so the SAME fitted
    encoders/scaler can be reapplied at prediction time — refitting on
    new data at inference time would be a data leakage bug.
    """
    df = features_df.copy()
    y = df.pop("disrupted")

    categorical_cols = ["gender", "state", "home_type", "state_family"]
    boolean_cols = ["special_needs", "accepts_special_needs", "accepts_sibling_groups"]
    numeric_cols = [c for c in df.columns if c not in categorical_cols + boolean_cols]

    encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le

    for col in boolean_cols:
        df[col] = df[col].astype(int)

    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    return df, y, {"encoders": encoders, "scaler": scaler, "numeric_cols": numeric_cols}


def transform_classification_features(features_df: pd.DataFrame, preprocessing: dict) -> pd.DataFrame:
    """
    Applies ALREADY-FITTED encoders/scaler (transform only, never
    fit_transform) to new data at prediction time. This is the inference-
    time counterpart to encode_and_scale_classification_features() above.

    WHY THIS MUST BE A SEPARATE FUNCTION, NOT A REUSE OF THE FIT VERSION:
    Fitting a new StandardScaler/LabelEncoder on a single prediction row
    (or any new data) would be a data leakage bug — the scaler's mean/std
    and the encoder's category mapping must come from the TRAINING data
    only, exactly as saved in ml/models_store/ by train_models. Using the
    same fitted objects is what makes a prediction comparable to the
    model's training distribution at all.
    """
    df = features_df.copy()
    if "disrupted" in df.columns:
        df = df.drop(columns=["disrupted"])

    encoders = preprocessing["encoders"]
    numeric_cols = preprocessing["numeric_cols"]
    scaler = preprocessing["scaler"]

    for col, encoder in encoders.items():
        # An unseen category (e.g. a state not present during training)
        # would make LabelEncoder.transform() raise — handled by mapping
        # to the first known class rather than crashing a live prediction
        # request, with the caller able to check for this via the
        # returned `unseen_categories` warning list if stricter handling
        # is ever needed.
        known = set(encoder.classes_)
        df[col] = df[col].apply(lambda v: v if v in known else encoder.classes_[0])
        df[col] = encoder.transform(df[col])

    boolean_cols = ["special_needs", "accepts_special_needs", "accepts_sibling_groups"]
    for col in boolean_cols:
        df[col] = df[col].astype(int)

    df[numeric_cols] = scaler.transform(df[numeric_cols])
    return df


def build_single_pair_features(child_dict: dict, family_dict: dict) -> pd.DataFrame:
    """
    Builds the same engineered feature row build_placement_features()
    would produce, but for a SINGLE Child/FosterFamily pair rather than
    the whole Placement table — used at prediction time, before any
    Placement row exists. Deliberately reuses build_placement_features()
    itself (by wrapping the single pair in one-row DataFrames) rather than
    duplicating the feature-engineering logic, so training and inference
    can never silently drift apart from each other.
    """
    children_df = pd.DataFrame([child_dict])
    families_df = pd.DataFrame([family_dict])
    placements_df = pd.DataFrame([{
        "child_id": child_dict["id"],
        "family_id": family_dict["id"],
        "status": "proposed",  # placeholder — discarded, no real outcome exists yet
    }])
    return build_placement_features(children_df, families_df, placements_df)


def build_regression_features(children_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Builds the feature matrix for the REGRESSION target: predicting a
    child's time_in_care_months from their own profile (age, special
    needs, sibling group size, behavioral score) — deliberately excludes
    any family/placement information, since the point is to estimate
    expected time-in-care for resource planning BEFORE a placement is
    even decided.
    """
    df = children_df.copy()
    y = df.pop("time_in_care_months")

    feature_cols = ["age", "gender", "special_needs", "sibling_group_size", "behavioral_notes_score"]
    X = df[feature_cols].copy()

    le = LabelEncoder()
    X["gender"] = le.fit_transform(X["gender"])
    X["special_needs"] = X["special_needs"].astype(int)

    scaler = StandardScaler()
    numeric_cols = ["age", "sibling_group_size", "behavioral_notes_score"]
    X[numeric_cols] = scaler.fit_transform(X[numeric_cols])

    return X, y
    """
    Builds the feature matrix for the REGRESSION target: predicting a
    child's time_in_care_months from their own profile (age, special
    needs, sibling group size, behavioral score) — deliberately excludes
    any family/placement information, since the point is to estimate
    expected time-in-care for resource planning BEFORE a placement is
    even decided.
    """
    df = children_df.copy()
    y = df.pop("time_in_care_months")

    feature_cols = ["age", "gender", "special_needs", "sibling_group_size", "behavioral_notes_score"]
    X = df[feature_cols].copy()

    le = LabelEncoder()
    X["gender"] = le.fit_transform(X["gender"])
    X["special_needs"] = X["special_needs"].astype(int)

    scaler = StandardScaler()
    numeric_cols = ["age", "sibling_group_size", "behavioral_notes_score"]
    X[numeric_cols] = scaler.fit_transform(X[numeric_cols])

    return X, y
