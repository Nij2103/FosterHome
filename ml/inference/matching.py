"""
ml.inference.matching

Smart Matching Recommendations Engine.

Provides candidate filtering and ranking functions to recommend suitable
foster care placement matches for a given child or foster family.

PRODUCTION RULES & CONSTRAINTS:
1. Hard Cultural & Language Safety Filters:
   - Pre-filters critical language barriers where family cannot accommodate child's language.
2. Strict Sibling Group Integrity:
   - Family available capacity MUST be >= child's sibling group size (no splitting sibling groups).
   - If sibling_group_size > 1, family.accepts_sibling_groups MUST be True.
3. Capacity Check & Special Needs Pre-filters.
4. ML Compatibility Threshold & Ranking.
"""

from typing import Any, Dict, List, Optional
from apps.children.models import Child
from apps.families.models import FosterFamily
from ml.inference.predict import predict_compatibility, ModelNotTrainedError


def check_language_cultural_compatibility(child: Child, family: FosterFamily) -> bool:
    """
    Hard Pre-Filter Rule 1: Checks for critical language & cultural barriers.
    If the child requires a specific primary language accommodation,
    the foster family's language profile must accommodate it.
    """
    child_text = f"{child.case_notes} {child.ethnicity} {child.nationality} {getattr(child, 'languages_spoken', '')} {child.dietary_preferences}".lower()
    family_langs = [lang.strip().lower() for lang in family.languages_spoken.split(",") if lang.strip()]

    # Specific non-English primary language indicators
    critical_languages = {
        "spanish": ["spanish", "espanol", "español"],
        "french": ["french", "francais", "français"],
        "vietnamese": ["vietnamese"],
        "hindi": ["hindi"],
        "asl": ["asl", "sign language"],
    }

    for lang_key, keywords in critical_languages.items():
        if any(kw in child_text for kw in keywords):
            # Child requires this language accommodation
            family_has_lang = any(
                any(kw in fam_lang for kw in keywords) for fam_lang in family_langs
            )
            if not family_has_lang:
                return False  # Critical language barrier flagged

    return True


def find_suitable_matches_for_child(
    child: Child,
    min_score: float = 0.40,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Finds and ranks suitable candidate Foster Families for a given Child.
    Returns a list of dicts with family info, compatibility score, and match badge.
    """
    candidate_families = FosterFamily.objects.filter(is_active=True)
    suitable_matches = []

    for family in candidate_families:
        # Rule 2: Strict Sibling Group Integrity & Capacity Check
        available_slots = family.capacity - family.current_occupancy
        if available_slots < child.sibling_group_size:
            continue  # Do not allow splitting sibling groups

        if child.sibling_group_size > 1 and not family.accepts_sibling_groups:
            continue

        # Hard Constraint: Special needs check
        if child.special_needs and not family.accepts_special_needs:
            continue

        # Rule 1: Hard Cultural & Language Safety Filter
        if not check_language_cultural_compatibility(child, family):
            continue

        # Run ML inference
        try:
            result = predict_compatibility(child, family)
            score = float(result["compatibility_score"])
        except Exception:
            from ml.inference.predict import compute_compatibility_features
            feats = compute_compatibility_features(child, family)
            score = feats["composite_score"]
            result = {
                "compatibility_score": score,
                "explanation": {"summary_text": f"Compatibility score: {int(score*100)}%"},
            }

        # ML Compatibility Threshold check
        if score < min_score:
            continue

        # Badge determination
        if score >= 0.75:
            badge_class = "success"
            badge_label = "High Match"
        elif score >= 0.60:
            badge_class = "primary"
            badge_label = "Good Match"
        else:
            badge_class = "warning"
            badge_label = "Moderate Match"

        suitable_matches.append({
            "id": family.pk,
            "name": family.family_name,
            "state": family.state,
            "capacity": family.capacity,
            "available_slots": family.available_slots,
            "experience_years": family.experience_years,
            "home_type": family.get_home_type_display(),
            "compatibility_score": score,
            "score_percent": int(round(score * 100)),
            "badge_class": badge_class,
            "badge_label": badge_label,
            "explanation_summary": result.get("explanation", {}).get("summary_text", "") if isinstance(result, dict) else "",
        })

    suitable_matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return suitable_matches[:max_results]


def find_suitable_matches_for_family(
    family: FosterFamily,
    min_score: float = 0.40,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Finds and ranks suitable candidate Children for a given Foster Family.
    Returns a list of dicts with child info, compatibility score, and match badge.
    """
    available_slots = family.capacity - family.current_occupancy
    if available_slots <= 0:
        return []

    candidate_children = Child.objects.filter(is_placed=False)
    suitable_matches = []

    for child in candidate_children:
        # Rule 2: Strict Sibling Group Integrity & Capacity Check
        if available_slots < child.sibling_group_size:
            continue

        if child.sibling_group_size > 1 and not family.accepts_sibling_groups:
            continue

        # Hard Constraint: Special needs check
        if child.special_needs and not family.accepts_special_needs:
            continue

        # Rule 1: Hard Cultural & Language Safety Filter
        if not check_language_cultural_compatibility(child, family):
            continue

        # Run ML inference
        try:
            result = predict_compatibility(child, family)
            score = float(result["compatibility_score"])
        except Exception:
            from ml.inference.predict import compute_compatibility_features
            feats = compute_compatibility_features(child, family)
            score = feats["composite_score"]
            result = {
                "compatibility_score": score,
                "explanation": {"summary_text": f"Compatibility score: {int(score*100)}%"},
            }

        # ML Compatibility Threshold check
        if score < min_score:
            continue

        if score >= 0.75:
            badge_class = "success"
            badge_label = "High Match"
        elif score >= 0.60:
            badge_class = "primary"
            badge_label = "Good Match"
        else:
            badge_class = "warning"
            badge_label = "Moderate Match"

        suitable_matches.append({
            "id": child.pk,
            "name": child.first_name,
            "age": child.age,
            "gender": child.get_gender_display(),
            "state": child.state,
            "special_needs": child.special_needs,
            "sibling_group_size": child.sibling_group_size,
            "time_in_care_months": child.time_in_care_months,
            "compatibility_score": score,
            "score_percent": int(round(score * 100)),
            "badge_class": badge_class,
            "badge_label": badge_label,
            "explanation_summary": result.get("explanation", {}).get("summary_text", "") if isinstance(result, dict) else "",
        })

    suitable_matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return suitable_matches[:max_results]
