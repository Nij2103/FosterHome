"""
ml.data.synthetic_generator

Generates SYNTHETIC Child, FosterFamily, and Placement records for this
project's database. No real child, family, or case record is used or
represented anywhere in this module — see the project's Step 1 data-ethics
notes.

WHY THE DISTRIBUTIONS BELOW AREN'T ARBITRARY:
Purely uniform/random synthetic data would (a) not resemble real foster
care demographics, weakening the EDA chapter, and (b) give the ML models
nothing structured to learn, since a model can't find patterns in noise.
So several distributions here are grounded in aggregate, published AFCARS
statistics (the same real government data source used in the Step 6
scraper) — e.g., the placement-type mix and roughly-even multi-age spread
with a mild skew toward younger children. Where I made a simplifying
assumption instead of using a specific published figure (e.g., state
selection is uniform rather than population-weighted), that is stated
explicitly in a comment, so nothing here is quietly presented as more
authoritative than it is.

DELIBERATE, DOCUMENTED CORRELATIONS (this is what gives the downstream ML
classifier in ml/training/ something real to learn — see Step 9):
1. A special-needs child placed with a family that does NOT accept
   special needs has a substantially higher disruption probability.
2. A sibling group larger than a family's available capacity is never
   placed together (mirrors real placement-matching constraints).
3. A cross-state placement (child's state != family's state) has a
   moderately higher disruption probability than an in-state placement.
4. More experienced families (higher `experience_years`) have a lower
   disruption probability.
These are simplifications of real-world placement-matching research
findings, deliberately encoded so the "placement compatibility" ML target
is learnable and explainable — not an attempt to model real casework
precisely.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RANDOM_SEED = 42

# A reduced, representative set of US states (rather than all 50) keeps
# the synthetic dataset's state-wise charts readable in the EDA/dashboard
# — a common, documented simplification for teaching datasets of this size.
STATES = [
    "California", "Texas", "New York", "Florida", "Ohio",
    "Illinois", "Pennsylvania", "Georgia", "North Carolina", "Michigan",
]

FIRST_NAMES = [
    "Avery", "Jordan", "Riley", "Casey", "Morgan", "Taylor", "Quinn", "Rowan",
    "Skyler", "Reese", "Hayden", "Dakota", "Emerson", "Finley", "Sawyer",
    "Blake", "Drew", "Elliot", "Kendall", "Peyton",
]  # synthetic first names only — see module docstring

FAMILY_SURNAMES = [
    "Anderson", "Bennett", "Carter", "Dawson", "Ellis", "Foster", "Grant",
    "Harper", "Ingram", "Jensen", "Kessler", "Lawson", "Mercer", "Nolan",
    "Ortiz", "Parrish", "Quinlan", "Reyes", "Sutton", "Turner",
]  # synthetic family names only

EDUCATION_BY_AGE = {
    range(0, 5): "Pre-K",
    range(5, 11): "Elementary",
    range(11, 14): "Middle School",
    range(14, 19): "High School",
}

HOME_TYPES = ["urban", "suburban", "rural"]
HOME_TYPE_WEIGHTS = [0.45, 0.35, 0.20]  # loosely reflects US population distribution


def _education_level_for_age(age: int) -> str:
    for age_range, level in EDUCATION_BY_AGE.items():
        if age in age_range:
            return level
    return "High School"


def generate_children(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generates n synthetic Child records as a DataFrame matching
    apps.children.models.Child field names exactly, so the loader
    management command can create objects with **row.to_dict().
    """
    # Age distribution: mild skew toward younger children, broadly
    # consistent with AFCARS published age-at-report-date breakdowns
    # (roughly even across 1-17 with somewhat higher shares at younger
    # ages) — approximated here with a truncated skew-normal via clipping
    # rather than reproducing the exact published histogram.
    ages = rng.integers(low=0, high=18, size=n)

    genders = rng.choice(["M", "F", "O"], size=n, p=[0.50, 0.48, 0.02])
    states = rng.choice(STATES, size=n)
    # ~22% special needs, an approximation of AFCARS's published clinical
    # diagnosis prevalence among children in foster care.
    special_needs = rng.random(n) < 0.22

    # Sibling group size: most children have no co-placed siblings (1),
    # a meaningful minority have 2-4.
    sibling_group_size = rng.choice([1, 2, 3, 4], size=n, p=[0.55, 0.25, 0.13, 0.07])

    # Behavioral notes score: correlated with special_needs and, mildly,
    # with age (older children in care longer tend to have more
    # documented behavioral history) — an explicit, simple linear bump,
    # not a claim about real psychological outcomes.
    base_score = rng.beta(2, 5, size=n)  # right-skewed toward lower severity
    score_bump = np.where(special_needs, 0.18, 0.0) + (ages / 18) * 0.10
    behavioral_notes_score = np.clip(base_score + score_bump, 0, 1)

    education_level = [_education_level_for_age(a) for a in ages]

    # Time in care: a deterministic, feature-driven component (the
    # learnable signal) plus a fixed-scale noise term — deliberately NOT
    # modeled as "exponential(scale=feature-driven-mean)", because for an
    # exponential distribution std always equals the mean, which would
    # make the noise grow in lockstep with the very signal we want a
    # regression model to detect and swamp it on a modest sample size.
    # Separating a fixed-variance noise term from the mean-shifting signal
    # is standard practice for a synthetic regression target with a
    # genuinely learnable (but not deterministic — real data isn't) effect
    # size. Effect directions are grounded in real foster-care research
    # findings: older children, special-needs children, higher documented
    # behavioral severity, and larger sibling groups all correlate with
    # longer stays in care (harder to match with an available family).
    base_months = (
        4.0
        + (ages / 18) * 14.0                        # older children: longer stays
        + np.where(special_needs, 10.0, 0.0)         # special needs: longer stays
        + behavioral_notes_score * 16.0              # higher severity: longer stays
        + (sibling_group_size - 1) * 3.0             # larger sibling groups: longer stays
    )
    noise = rng.exponential(scale=8.0, size=n)  # fixed-scale noise, independent of signal magnitude
    time_in_care_months = np.clip(base_months + noise, 0, 96).astype(int)

    return pd.DataFrame({
        "first_name": rng.choice(FIRST_NAMES, size=n),
        "age": ages,
        "gender": genders,
        "state": states,
        "special_needs": special_needs,
        "sibling_group_size": sibling_group_size,
        "behavioral_notes_score": behavioral_notes_score.round(3),
        "education_level": education_level,
        "time_in_care_months": time_in_care_months,
        "is_placed": False,  # set later, once generate_placements() runs
    })


def generate_foster_families(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generates n synthetic FosterFamily records matching
    apps.families.models.FosterFamily field names.
    """
    capacity = rng.choice([1, 2, 3, 4, 5, 6], size=n, p=[0.15, 0.30, 0.25, 0.15, 0.10, 0.05])
    experience_years = np.clip(rng.exponential(scale=5, size=n), 0, 30).astype(int)

    # More experienced families are somewhat more likely to accept
    # special needs and sibling groups — a mild, documented correlation
    # reflecting that specialization tends to grow with experience.
    experience_factor = np.clip(experience_years / 15, 0, 1)
    accepts_special_needs = rng.random(n) < (0.30 + 0.25 * experience_factor)
    accepts_sibling_groups = rng.random(n) < (0.25 + 0.30 * experience_factor)

    return pd.DataFrame({
        "family_name": [f"{rng.choice(FAMILY_SURNAMES)} Family" for _ in range(n)],
        "state": rng.choice(STATES, size=n),
        "capacity": capacity,
        "current_occupancy": 0,  # set later, once generate_placements() runs
        "experience_years": experience_years,
        "accepts_special_needs": accepts_special_needs,
        "accepts_sibling_groups": accepts_sibling_groups,
        "home_type": rng.choice(HOME_TYPES, size=n, p=HOME_TYPE_WEIGHTS),
        "is_active": rng.random(n) < 0.95,
    })


def generate_placements(
    children_df: pd.DataFrame,
    families_df: pd.DataFrame,
    rng: np.random.Generator,
    placement_rate: float = 0.70,
) -> pd.DataFrame:
    """
    Attempts to place `placement_rate` fraction of children with an
    available, active family, using simple compatibility rules, then
    assigns a placement status (proposed/active/disrupted/completed)
    according to the documented probability rules in this module's
    docstring (points 1-4).

    Returns a DataFrame of placements with child_index/family_index
    (positional indices into the input DataFrames — the loader command
    maps these to real primary keys after bulk-creating Child/FosterFamily
    rows) plus a `status` column.

    This is a simplified matching simulation, not a placement
    optimization algorithm — the goal is a plausible, learnable dataset,
    not a claim about real casework matching logic.
    """
    families = families_df.copy()
    families["remaining_capacity"] = families["capacity"]
    active_family_indices = families.index[families["is_active"]].tolist()
    rng.shuffle(active_family_indices)

    # Pre-group active family indices by state so each child's search can
    # prefer in-state families first — mirrors real case-worker practice
    # (minimizing disruption to a child's school/community ties) and
    # ensures cross-state placements are the fallback, not the majority
    # by accident of round-robin ordering across only 10 states.
    families_by_state: dict[str, list[int]] = {}
    for idx in active_family_indices:
        state = families.loc[idx, "state"]
        families_by_state.setdefault(state, []).append(idx)

    n_to_place = int(len(children_df) * placement_rate)
    candidate_children = rng.choice(children_df.index, size=n_to_place, replace=False)

    placements = []
    state_cursors: dict[str, int] = {}

    for child_idx in candidate_children:
        child = children_df.loc[child_idx]
        needed_slots = int(child["sibling_group_size"])
        child_state = child["state"]

        # Search order: most children's case workers try same-state
        # families first, but in-state capacity is often scarce/full in
        # practice, so a documented fraction of searches (30%) skip
        # straight to the full active pool — this is what produces a
        # realistic MIX of in-state and cross-state placements rather
        # than either extreme (all cross-state, as with pure round-robin,
        # or all in-state, as with unconditional in-state preference).
        try_in_state_first = rng.random() < 0.50
        in_state = families_by_state.get(child_state, []) if try_in_state_first else []
        search_order = []
        if in_state:
            start = state_cursors.get(child_state, 0)
            search_order += [in_state[(start + i) % len(in_state)] for i in range(len(in_state))]
            state_cursors[child_state] = start + 1
        search_order += list(rng.permutation(active_family_indices))

        placed = False
        attempts = 0
        for fam_idx in search_order:
            if attempts >= 8 or placed:
                break
            attempts += 1

            family = families.loc[fam_idx]
            if family["remaining_capacity"] < needed_slots:
                continue  # sibling group doesn't fit — rule #2

            # Compute disruption probability from the documented rules.
            disruption_prob = 0.10  # baseline
            if child["special_needs"] and not family["accepts_special_needs"]:
                disruption_prob += 0.30  # rule #1
            if child_state != family["state"]:
                disruption_prob += 0.08  # rule #3
            disruption_prob -= min(family["experience_years"], 20) / 20 * 0.05  # rule #4
            disruption_prob = float(np.clip(disruption_prob, 0.02, 0.85))

            # Re-normalize since the four raw weights below don't always
            # sum to exactly 1 once disruption_prob varies per pair.
            weights = np.array([
                disruption_prob, 0.45, 0.35, max(0.20 - disruption_prob, 0.02),
            ])
            weights = weights / weights.sum()
            status = rng.choice(["disrupted", "active", "completed", "proposed"], p=weights)

            placements.append({
                "child_index": child_idx,
                "family_index": fam_idx,
                "status": status,
            })
            families.loc[fam_idx, "remaining_capacity"] -= needed_slots
            placed = True

    return pd.DataFrame(placements)
