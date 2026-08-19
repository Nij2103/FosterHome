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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, View

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin, role_required
from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.predictions.forms import PredictionRequestForm
from apps.predictions.models import Prediction
from ml.inference.predict import IncompleteProfileError, ModelNotTrainedError, predict_compatibility


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

    def _get_viewer_context(self, request):
        is_viewer = False
        user_family_count = 0
        if request.user.is_authenticated and not request.user.is_superuser:
            profile = getattr(request.user, "profile", None)
            if profile and profile.is_viewer:
                is_viewer = True
                user_family_count = FosterFamily.objects.filter(created_by=request.user).count()
        return is_viewer, user_family_count

    def get(self, request):
        initial = {}
        child_id = request.GET.get("child")
        if child_id:
            initial["child"] = child_id

        is_viewer, user_family_count = self._get_viewer_context(request)
        form = PredictionRequestForm(initial=initial, user=request.user)

        return render(
            request,
            "predictions/prediction_form.html",
            {
                "form": form,
                "is_viewer": is_viewer,
                "user_family_count": user_family_count,
            },
        )

    def post(self, request):
        is_viewer, user_family_count = self._get_viewer_context(request)

        if is_viewer and user_family_count == 0:
            messages.error(
                request,
                "As a Viewer, you must add at least one foster family before requesting predictions.",
            )
            return redirect("families:create")

        form = PredictionRequestForm(request.POST, user=request.user)
        if not form.is_valid():
            return render(
                request,
                "predictions/prediction_form.html",
                {
                    "form": form,
                    "is_viewer": is_viewer,
                    "user_family_count": user_family_count,
                },
            )

        child = form.cleaned_data["child"]
        family = form.cleaned_data["family"]

        if is_viewer and family.created_by != request.user:
            messages.error(
                request,
                "As a Viewer, you can only request predictions for foster families created by you.",
            )
            return redirect("predictions:create")

        try:
            result = predict_compatibility(child, family)
        except IncompleteProfileError as e:
            messages.error(
                request,
                f"Prediction Disabled: 100% Profile Completion is required for both Child and Foster Family before running predictions. {str(e)}",
            )
            return render(
                request,
                "predictions/prediction_form.html",
                {
                    "form": form,
                    "is_viewer": is_viewer,
                    "user_family_count": user_family_count,
                },
            )
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
            model_version=result.get("model_version", "v2.0"),
            predicted_by=request.user,
            explanation_data=result.get("explanation", {}),
        )

        return redirect("predictions:detail", pk=prediction.pk)



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
