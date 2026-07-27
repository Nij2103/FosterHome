"""
apps.predictions.views

The prediction-request view is where Step 9's persisted model actually
gets used by the web application — everything before this (training,
comparison, persistence) was building toward this moment. Predictions are
readable by all roles; requesting a NEW prediction is restricted to
Admin/Case Worker (a Viewer can see past predictions but shouldn't be able
to spend model-inference resources triggering new ones, consistent with
the read-only role design from Step 5).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin, role_required
from apps.children.models import Child
from apps.core.exports import export_as_csv
from apps.predictions.forms import PredictionRequestForm
from apps.predictions.models import Prediction
from ml.inference.predict import ModelNotTrainedError, predict_compatibility

PREDICTION_EXPORT_COLUMNS = [
    ("Child", lambda p: p.child.first_name),
    ("Family", lambda p: p.family.family_name),
    ("Compatibility Score", lambda p: p.compatibility_score),
    ("Model", lambda p: p.model_name),
    ("Model Version", lambda p: p.model_version),
    ("Requested By", lambda p: p.predicted_by.username if p.predicted_by else ""),
    ("Date", lambda p: p.created_at.strftime("%Y-%m-%d")),
]


def filter_predictions_queryset(request):
    qs = Prediction.objects.select_related("child", "family").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(Q(child__first_name__icontains=query) | Q(family__family_name__icontains=query))
    return qs


class PredictionListView(LoginRequiredMixin, ListView):
    model = Prediction
    template_name = "predictions/prediction_list.html"
    context_object_name = "predictions"
    paginate_by = 20

    def get_queryset(self):
        return filter_predictions_queryset(self.request)


@login_required
def export_predictions_csv(request):
    qs = filter_predictions_queryset(request)
    return export_as_csv(qs, PREDICTION_EXPORT_COLUMNS, "predictions_export")


class PredictionDetailView(LoginRequiredMixin, DetailView):
    model = Prediction
    template_name = "predictions/prediction_detail.html"
    context_object_name = "prediction"


class PredictionCreateView(RoleRequiredMixin, LoginRequiredMixin, View):
    """
    Implemented as a plain function-style view via get/post rather than
    Django's generic CreateView, since this doesn't create a Prediction
    directly from form fields — it runs model inference first (see
    ml.inference.predict) and the Prediction row is a RESULT of that
    computation, not a direct user-submitted record.
    """
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER, Profile.Role.VIEWER)

    def get(self, request):
        initial = {}
        child_id = request.GET.get("child")
        if child_id:
            initial["child"] = child_id
        form = PredictionRequestForm(initial=initial)
        return render(request, "predictions/prediction_form.html", {"form": form})

    def post(self, request):
        form = PredictionRequestForm(request.POST)
        if not form.is_valid():
            return render(request, "predictions/prediction_form.html", {"form": form})

        child = form.cleaned_data["child"]
        family = form.cleaned_data["family"]

        try:
            result = predict_compatibility(child, family)
        except ModelNotTrainedError:
            messages.error(
                request,
                "No trained model is available yet. An administrator needs to run "
                "`python manage.py train_models` before predictions can be made.",
            )
            return redirect("predictions:create")

        prediction = Prediction.objects.create(
            child=child,
            family=family,
            compatibility_score=result["compatibility_score"],
            model_name=result["model_name"],
            model_version="v1",
            predicted_by=request.user,
            explanation_data=result.get("explanation", {}),
        )

        messages.success(
            request,
            f"Prediction complete: {child.first_name} \u00d7 {family.family_name} "
            f"scored {result['compatibility_score']:.2f} compatibility "
            f"(using {result['model_name']}).",
        )
        return redirect("predictions:detail", pk=prediction.pk)


@login_required
def export_prediction_pdf(request, pk):
    """
    Generates a professional single-prediction PDF report using
    reportlab's Platypus layer (the same approach used for the AFCARS
    fixture in Step 6) — a formatted document with a title, a
    child/family summary table, and the score, not just text dumped onto
    a page.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    prediction = Prediction.objects.select_related("child", "family", "predicted_by").get(pk=pk)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="prediction_{prediction.pk}_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Foster Care Placement Compatibility Report", styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Generated {prediction.created_at.strftime('%B %d, %Y')} by {prediction.predicted_by.username if prediction.predicted_by else 'system'}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 20))

    score_color = "#1e7e34" if prediction.compatibility_score >= 0.7 else (
        "#b8860b" if prediction.compatibility_score >= 0.4 else "#c0392b"
    )
    # A Paragraph's line spacing (leading) is derived from its STYLE, not
    # from any inline <font size="..."> tags used within it — mixing a
    # 28pt score and 12pt caption inside one styles["Normal"]-based
    # paragraph left the paragraph's box sized for 12pt text while the
    # actual rendered glyphs were 28pt, causing it to overlap the next
    # element. Fixed with a dedicated style carrying the correct leading.
    from reportlab.lib.styles import ParagraphStyle
    score_style = ParagraphStyle("ScoreStyle", parent=styles["Normal"], fontSize=28, leading=34)
    story.append(Paragraph(
        f'<font color="{score_color}"><b>{prediction.compatibility_score:.2f}</b></font>',
        score_style,
    ))
    story.append(Paragraph("predicted compatibility score", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Model: {prediction.model_name} ({prediction.model_version})", styles["Normal"]))
    story.append(Spacer(1, 20))

    data = [
        ["", "Child", "Foster Family"],
        ["Name", prediction.child.first_name, prediction.family.family_name],
        ["State", prediction.child.state, prediction.family.state],
        ["Age / Experience", str(prediction.child.age), f"{prediction.family.experience_years} yrs"],
        ["Special needs", "Yes" if prediction.child.special_needs else "No",
         "Accepts" if prediction.family.accepts_special_needs else "Does not accept"],
        ["Sibling group / Capacity", str(prediction.child.sibling_group_size),
         f"{prediction.family.available_slots} of {prediction.family.capacity} available"],
    ]
    table = Table(data, colWidths=[1.8 * inch, 2.3 * inch, 2.3 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a7ca5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f5f5f0")),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    if prediction.summary_explanation_text:
        story.append(Paragraph("<b>Explainable AI (SHAP Feature Attribution Analysis)</b>", styles["Heading3"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<i>{prediction.summary_explanation_text}</i>", styles["Normal"]))
        story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<i>This score is a decision-support estimate produced by a machine learning model "
        "trained on historical placement outcomes. It is not a placement decision and should "
        "be reviewed by a qualified case worker alongside other factors, per standard casework "
        "practice.</i>",
        styles["Normal"],
    )
)

    doc.build(story)
    return response


@role_required("admin", "caseworker")
def suitable_matches_api(request):
    """
    AJAX endpoint for the Smart Matching engine.
    Restricted to Admin and Case Worker roles.
    Query parameters:
      ?child_id=X -> Returns ranked suitable candidate Foster Families for child X
      ?family_id=Y -> Returns ranked suitable candidate Children for family Y
    """
    from django.http import JsonResponse
    from apps.families.models import FosterFamily
    from ml.inference.matching import find_suitable_matches_for_child, find_suitable_matches_for_family

    child_id = request.GET.get("child_id")
    family_id = request.GET.get("family_id")
    try:
        min_score = float(request.GET.get("min_score", 0.35))
    except (ValueError, TypeError):
        min_score = 0.35

    if child_id:
        try:
            child = Child.objects.get(pk=child_id)
            matches = find_suitable_matches_for_child(child, min_score=min_score)
            return JsonResponse({"mode": "child", "target_id": child.pk, "matches": matches})
        except Child.DoesNotExist:
            return JsonResponse({"error": "Child record not found"}, status=404)

    elif family_id:
        try:
            family = FosterFamily.objects.get(pk=family_id)
            matches = find_suitable_matches_for_family(family, min_score=min_score)
            return JsonResponse({"mode": "family", "target_id": family.pk, "matches": matches})
        except FosterFamily.DoesNotExist:
            return JsonResponse({"error": "Foster family record not found"}, status=404)


    return JsonResponse({"matches": []})

