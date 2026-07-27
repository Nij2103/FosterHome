"""
apps.analytics.views

Dashboard (real DB-backed statistics + key charts), a full visualizations
gallery (every chart from Steps 8-9), and a model comparison page that
renders the actual ml_report.md produced by Step 9's train_models command.
"""

import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from apps.predictions.models import Prediction
from apps.reports.models import Report


@login_required
def dashboard(request):
    charts_dir = Path(settings.MEDIA_ROOT) / "analytics" / "charts"
    highlight_charts = [
        name for name in [
            "age_distribution.png", "placement_status_counts.png",
            "model_comparison_f1.png", "state_wise_children.png",
        ] if (charts_dir / name).exists()
    ]

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
        "highlight_charts": highlight_charts,
    }
    return render(request, "analytics/dashboard.html", context)


@login_required
def visualizations(request):
    charts_dir = Path(settings.MEDIA_ROOT) / "analytics" / "charts"
    chart_files = sorted(p.name for p in charts_dir.glob("*.png")) if charts_dir.exists() else []

    # Group charts by category for a more organized gallery, based on
    # filename prefixes established by run_eda.py / train_models.py.
    categories = {
        "Data Quality & Distributions": [f for f in chart_files if f in (
            "missing_values.png", "age_distribution.png", "gender_distribution.png",
            "state_wise_children.png", "special_needs_by_placement.png",
            "family_capacity_distribution.png", "home_type_distribution.png",
        )],
        "Correlation & Outliers": [f for f in chart_files if f in (
            "correlation_heatmap.png", "outlier_boxplot_time_in_care.png",
            "violin_behavioral_score.png", "pairplot_numeric_features.png",
        )],
        "Placements": [f for f in chart_files if f in (
            "placement_status_counts.png", "experience_vs_disruption.png",
        )],
        "Real Government Data Trends (AFCARS)": [f for f in chart_files if f.startswith("trend_")],
        "Model Evaluation": [f for f in chart_files if f.startswith("confusion_matrix_")
                              or f in ("roc_curves_comparison.png", "precision_recall_curves.png",
                                       "feature_importance.png", "model_comparison_accuracy.png",
                                       "model_comparison_f1.png", "regression_predicted_vs_actual.png")],
    }
    return render(request, "analytics/visualizations.html", {"categories": categories})


@login_required
def model_comparison(request):
    report_path = Path(settings.BASE_DIR) / "docs" / "ml_report.md"
    metadata_path = Path(settings.ML_MODELS_DIR) / "best_classifier_metadata.json"

    report_text = report_path.read_text() if report_path.exists() else None
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else None

    return render(request, "analytics/model_comparison.html", {
        "report_text": report_text,
        "metadata": metadata,
    })


@login_required
def export_dashboard_pdf(request):
    """
    A summary PDF combining live DB stats with actual generated chart
    images (embedded via reportlab's Image flowable, not re-rendered) —
    a genuinely useful "share this with someone who doesn't have access
    to the app" artifact, per the project brief's export requirements.
    """
    from django.http import HttpResponse
    from django.utils import timezone
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    charts_dir = Path(settings.MEDIA_ROOT) / "analytics" / "charts"

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="dashboard_summary.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Foster Care Placement Predictor - Dashboard Summary", styles["Title"]),
        Spacer(1, 4),
        Paragraph(f"Generated {timezone.now().strftime('%B %d, %Y')}", styles["Normal"]),
        Spacer(1, 16),
    ]

    stats_data = [
        ["Total Children", str(Child.objects.count()), "Placed", str(Child.objects.filter(is_placed=True).count())],
        ["Total Families", str(FosterFamily.objects.count()), "Active Placements", str(Placement.objects.filter(status="active").count())],
        ["Disrupted Placements", str(Placement.objects.filter(status="disrupted").count()), "Predictions Made", str(Prediction.objects.count())],
    ]
    table = Table(stats_data, colWidths=[1.7 * inch] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf4fb")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eaf7ee")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    for chart_name, caption in [
        ("age_distribution.png", "Age Distribution of Children in Care"),
        ("placement_status_counts.png", "Placement Outcomes"),
        ("model_comparison_f1.png", "ML Model Comparison (F1 Score)"),
    ]:
        chart_path = charts_dir / chart_name
        if chart_path.exists():
            story.append(Paragraph(caption, styles["Heading3"]))
            story.append(Image(str(chart_path), width=5.5 * inch, height=3.14 * inch))
            story.append(Spacer(1, 16))

    doc.build(story)
    return response
