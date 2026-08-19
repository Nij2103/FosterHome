"""
apps.placements.views
"""

import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin
from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.forms import PlacementForm
from apps.placements.models import Placement, PlacementOverrideLog


def filter_placements_queryset(request):
    qs = Placement.objects.select_related(
        "child", "family", "placed_by", "prediction"
    ).order_by("-created_at")

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(child__first_name__icontains=q) |
            Q(child__last_name__icontains=q) |
            Q(family__family_name__icontains=q) |
            Q(assigned_caseworker__icontains=q)
        )
    return qs


def placement_summary_api(request):
    """
    AJAX endpoint: returns a read-only summary card payload for a
    given child + family pair. Optionally returns prediction score
    if a prediction_id is supplied or one exists for the pair.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    child_id = request.GET.get("child_id")
    family_id = request.GET.get("family_id")
    prediction_id = request.GET.get("prediction_id")

    if not child_id or not family_id:
        return JsonResponse({"error": "child_id and family_id required"}, status=400)

    try:
        child = Child.objects.get(pk=child_id)
        family = FosterFamily.objects.get(pk=family_id)
    except (Child.DoesNotExist, FosterFamily.DoesNotExist):
        return JsonResponse({"error": "Record not found"}, status=404)

    # Resolve compatibility score
    score = None
    pred_pk = None
    pred_label = None

    if prediction_id:
        from apps.predictions.models import Prediction
        try:
            pred = Prediction.objects.get(pk=prediction_id)
            score = pred.compatibility_score
            pred_pk = pred.pk
            pred_label = f"#{pred.pk} — {pred.model_name}"
        except Prediction.DoesNotExist:
            pass
    else:
        # Try to find most recent prediction for this pair
        from apps.predictions.models import Prediction
        pred = Prediction.objects.filter(
            child=child, family=family
        ).order_by("-created_at").first()
        if pred:
            score = pred.compatibility_score
            pred_pk = pred.pk
            pred_label = f"#{pred.pk} — {pred.model_name}"

    data = {
        "child": {
            "name": child.full_name,
            "age": child.age,
            "language": child.languages_spoken,
            "medical_needs_level": child.medical_needs_level,
        },
        "family": {
            "name": family.family_name,
            "capacity": family.capacity,
            "housing_stability": family.housing_stability,
            "parenting_experience": family.parenting_experience_years,
        },
        "prediction": {
            "pk": pred_pk,
            "label": pred_label,
            "score": round(score * 100, 1) if score is not None else None,
        },
    }
    return JsonResponse(data)


class PlacementListView(LoginRequiredMixin, ListView):
    model = Placement
    template_name = "placements/placement_list.html"
    context_object_name = "placements"
    paginate_by = 20

    def get_queryset(self):
        return filter_placements_queryset(self.request)


class PlacementDetailView(LoginRequiredMixin, DetailView):
    model = Placement
    template_name = "placements/placement_detail.html"
    context_object_name = "placement"


class PlacementCreateView(RoleRequiredMixin, LoginRequiredMixin, CreateView):
    model = Placement
    form_class = PlacementForm
    template_name = "placements/placement_form.html"
    success_url = reverse_lazy("placements:index")
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        # Auto-fill caseworker name from the logged-in user's profile
        user = self.request.user
        full_name = user.get_full_name().strip()
        initial["assigned_caseworker"] = full_name if full_name else user.username

        # Pre-populate from ?prediction=<pk> query param
        pred_pk = self.request.GET.get("prediction")
        if pred_pk:
            from apps.predictions.models import Prediction
            try:
                pred = Prediction.objects.select_related("child", "family").get(pk=pred_pk)
                initial["prediction"] = pred.pk
                initial["child"] = pred.child.pk
                initial["family"] = pred.family.pk
                initial["compatibility_score"] = pred.compatibility_score
            except Prediction.DoesNotExist:
                pass
        # Pre-populate child from ?child=<pk>
        child_pk = self.request.GET.get("child")
        if child_pk and "child" not in initial:
            initial["child"] = child_pk
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_create"] = True
        ctx["pred_pk"] = self.request.GET.get("prediction", "")
        return ctx

    def form_valid(self, form):
        placement = form.save(commit=False)
        placement.placed_by = self.request.user
        placement.save()
        messages.success(self.request, "Placement recorded successfully.")
        return redirect("placements:detail", pk=placement.pk)


class PlacementUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Placement
    form_class = PlacementForm
    template_name = "placements/placement_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_create"] = False
        return ctx

    def get_success_url(self):
        return reverse_lazy("placements:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        placement = form.save(commit=False)
        placement.save()
        messages.success(self.request, "Placement updated successfully.")
        return redirect(self.get_success_url())


class PlacementDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Placement
    template_name = "placements/placement_confirm_delete.html"
    success_url = reverse_lazy("placements:index")
    allowed_roles = (Profile.Role.ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, "Placement deleted.")
        return super().form_valid(form)
