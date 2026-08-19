"""
apps.analytics.services

Calculates analytics statistics dynamically using Django ORM queries.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone as dt_timezone
from django.db.models import Count, Q
from django.utils import timezone

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from apps.predictions.models import Prediction


def get_overview_metrics() -> dict:
    """
    Returns 5 key summary metrics:
    - Total Children
    - Total Foster Families
    - Total Predictions
    - Total Placements
    - Placement Success Rate (%)
    """
    total_children = Child.objects.count()
    total_families = FosterFamily.objects.count()
    total_predictions = Prediction.objects.count()
    total_placements = Placement.objects.count()

    if total_placements > 0:
        disrupted_count = Placement.objects.filter(status="disrupted").count()
        successful_count = total_placements - disrupted_count
        success_rate = round((successful_count / total_placements) * 100, 1)
    else:
        success_rate = 0.0

    return {
        "total_children": total_children,
        "total_families": total_families,
        "total_predictions": total_predictions,
        "total_placements": total_placements,
        "placement_success_rate": success_rate,
    }


def get_child_analytics_data() -> dict:
    """
    Returns child data distributions for:
    1. Age Distribution (binned into standard age groups)
    2. Primary Language Spoken Distribution
    """
    # Age distribution
    age_groups = {
        "0–3 yrs": Child.objects.filter(age__gte=0, age__lte=3).count(),
        "4–7 yrs": Child.objects.filter(age__gte=4, age__lte=7).count(),
        "8–11 yrs": Child.objects.filter(age__gte=8, age__lte=11).count(),
        "12–15 yrs": Child.objects.filter(age__gte=12, age__lte=15).count(),
        "16–18 yrs": Child.objects.filter(age__gte=16, age__lte=18).count(),
    }

    # Language distribution (top 6 languages + Other)
    lang_counts = Counter()
    for child in Child.objects.only("languages_spoken"):
        lang = str(child.languages_spoken).strip() if child.languages_spoken else "Not Specified"
        if lang.lower() == "none" or not lang:
            lang = "Not Specified"
        lang_counts[lang] += 1

    top_langs = dict(lang_counts.most_common(6))
    other_count = sum(count for lang, count in lang_counts.items() if lang not in top_langs)
    if other_count > 0:
        top_langs["Other"] = other_count

    return {
        "age_distribution": age_groups,
        "language_distribution": top_langs if top_langs else {"Not Specified": 1},
    }


def get_family_analytics_data() -> dict:
    """
    Returns foster family data distributions for:
    1. Family Capacity Distribution (number of children accepted)
    2. Housing Stability Distribution (High, Medium, Low)
    """
    # Capacity distribution
    capacity_qs = FosterFamily.objects.values("capacity").annotate(count=Count("id")).order_by("capacity")
    capacity_dist = {f"{item['capacity']} Child(ren)": item["count"] for item in capacity_qs}
    if not capacity_dist:
        capacity_dist = {"1 Child": 0}

    # Housing stability distribution
    stability_qs = FosterFamily.objects.values("housing_stability").annotate(count=Count("id"))
    stability_dist = Counter()
    for item in stability_qs:
        val = str(item["housing_stability"]).strip().title() if item["housing_stability"] else "High"
        if val.lower() in ("none", ""):
            val = "High"
        stability_dist[val] += item["count"]

    # Ensure all standard tiers are present in order
    ordered_stability = {}
    for tier in ["High", "Medium", "Low"]:
        if tier in stability_dist:
            ordered_stability[tier] = stability_dist[tier]
    for k, v in stability_dist.items():
        if k not in ordered_stability:
            ordered_stability[k] = v

    return {
        "capacity_distribution": capacity_dist,
        "housing_stability_distribution": ordered_stability if ordered_stability else {"High": 1},
    }


def get_prediction_analytics_data() -> dict:
    """
    Returns prediction data distributions for:
    1. Compatibility Score Distribution (0-20%, 21-40%, 41-60%, 61-80%, 81-100%)
    2. Risk Level Distribution (Low Risk, Moderate Risk, High Risk)
    """
    scores = list(Prediction.objects.values_list("compatibility_score", flat=True))
    score_bins = {
        "0–20%": 0,
        "21–40%": 0,
        "41–60%": 0,
        "61–80%": 0,
        "81–100%": 0,
    }

    for s in scores:
        pct = s * 100 if s <= 1.0 else s
        if pct <= 20:
            score_bins["0–20%"] += 1
        elif pct <= 40:
            score_bins["21–40%"] += 1
        elif pct <= 60:
            score_bins["41–60%"] += 1
        elif pct <= 80:
            score_bins["61–80%"] += 1
        else:
            score_bins["81–100%"] += 1

    # Risk level distribution
    risk_counts = Counter()
    predictions = Prediction.objects.only("explanation_data", "compatibility_score")
    for p in predictions:
        r_level = None
        if isinstance(p.explanation_data, dict):
            r_level = p.explanation_data.get("risk_level")
        
        if not r_level:
            # Fallback based on score
            pct = p.compatibility_score * 100 if p.compatibility_score <= 1.0 else p.compatibility_score
            if pct >= 75:
                r_level = "Low Risk"
            elif pct >= 50:
                r_level = "Moderate Risk"
            else:
                r_level = "High Risk"
        
        risk_counts[str(r_level).title()] += 1

    ordered_risk = {}
    for r in ["Low Risk", "Moderate Risk", "High Risk"]:
        if r in risk_counts:
            ordered_risk[r] = risk_counts[r]
    for k, v in risk_counts.items():
        if k not in ordered_risk:
            ordered_risk[k] = v

    return {
        "compatibility_score_distribution": score_bins,
        "risk_level_distribution": ordered_risk if ordered_risk else {"Low Risk": 1},
    }


def get_placement_analytics_data() -> dict:
    """
    Returns placement data distributions for:
    1. Placement Status Distribution (Active, Completed, Disrupted)
    2. Monthly Placement Trend (Past 6-12 months)
    """
    # Status distribution
    status_qs = Placement.objects.values("status").annotate(count=Count("id"))
    status_dist = {}
    for item in status_qs:
        st = str(item["status"]).replace("_", " ").title()
        status_dist[st] = item["count"]

    if not status_dist:
        status_dist = {"Active": 0, "Completed": 0, "Disrupted": 0}

    # Monthly placement trend (last 6 months)
    now = timezone.now()
    monthly_trend = {}
    for i in range(5, -1, -1):
        # Calculate month year label
        month_date = now - timedelta(days=i * 30)
        month_label = month_date.strftime("%b %Y")
        
        # Start and end of that month
        start_of_month = datetime(month_date.year, month_date.month, 1, tzinfo=dt_timezone.utc)
        if month_date.month == 12:
            end_of_month = datetime(month_date.year + 1, 1, 1, tzinfo=dt_timezone.utc)
        else:
            end_of_month = datetime(month_date.year, month_date.month + 1, 1, tzinfo=dt_timezone.utc)
            
        cnt = Placement.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month).count()
        monthly_trend[month_label] = cnt

    return {
        "placement_status_distribution": status_dist,
        "monthly_placement_trend": monthly_trend,
    }
