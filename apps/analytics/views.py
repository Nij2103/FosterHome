"""
apps.analytics.views

Executive Dashboard (real DB-backed statistics and operational metrics)
and dynamic SVG Analytics & Insights Dashboard.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render
from django.utils.safestring import mark_safe

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from apps.predictions.models import Prediction
from apps.reports.models import Report
from apps.analytics import charts, services


@login_required
def dashboard(request):
    """
    Renders the Executive Placement System Dashboard.
    """
    context = {
        "total_children": Child.objects.count(),
        "placed_children": Child.objects.filter(is_placed=True).count(),
        "total_families": FosterFamily.objects.count(),
        "available_families": FosterFamily.objects.filter(
            is_active=True, current_occupancy__lt=F("capacity"),
        ).count(),
        "active_placements": Placement.objects.filter(status="active").count(),
        "disrupted_placements": Placement.objects.filter(status="disrupted").count(),
        "total_predictions": Prediction.objects.count(),
        "total_reports": Report.objects.count(),
        "recent_placements": Placement.objects.select_related("child", "family").order_by("-created_at")[:5],
        "recent_predictions": Prediction.objects.select_related("child", "family").order_by("-created_at")[:5],
    }
    return render(request, "analytics/dashboard.html", context)


@login_required
def analytics_dashboard(request):
    """
    Renders the unified Analytics & Insights Dashboard.
    Workflow: DB -> Django ORM -> Services -> Matplotlib -> BytesIO -> SVG -> HTML Template
    """
    # 1. Overview Summary Cards
    overview_metrics = services.get_overview_metrics()

    # 2. Child Analytics Data & Charts
    child_data = services.get_child_analytics_data()
    child_age_svg = mark_safe(charts.generate_child_age_distribution_chart(child_data["age_distribution"]))
    child_lang_svg = mark_safe(charts.generate_child_language_distribution_chart(child_data["language_distribution"]))

    # 3. Foster Family Analytics Data & Charts
    family_data = services.get_family_analytics_data()
    family_capacity_svg = mark_safe(charts.generate_family_capacity_distribution_chart(family_data["capacity_distribution"]))
    family_stability_svg = mark_safe(charts.generate_family_housing_stability_chart(family_data["housing_stability_distribution"]))

    # 4. Prediction Analytics Data & Charts
    pred_data = services.get_prediction_analytics_data()
    pred_score_svg = mark_safe(charts.generate_compatibility_score_distribution_chart(pred_data["compatibility_score_distribution"]))
    pred_risk_svg = mark_safe(charts.generate_risk_level_distribution_chart(pred_data["risk_level_distribution"]))

    # 5. Placement Analytics Data & Charts
    placement_data = services.get_placement_analytics_data()
    placement_status_svg = mark_safe(charts.generate_placement_status_distribution_chart(placement_data["placement_status_distribution"]))
    placement_trend_svg = mark_safe(charts.generate_monthly_placement_trend_chart(placement_data["monthly_placement_trend"]))

    context = {
        "overview": overview_metrics,
        "child_age_svg": child_age_svg,
        "child_lang_svg": child_lang_svg,
        "family_capacity_svg": family_capacity_svg,
        "family_stability_svg": family_stability_svg,
        "pred_score_svg": pred_score_svg,
        "pred_risk_svg": pred_risk_svg,
        "placement_status_svg": placement_status_svg,
        "placement_trend_svg": placement_trend_svg,
    }

    return render(request, "analytics/analytics.html", context)
