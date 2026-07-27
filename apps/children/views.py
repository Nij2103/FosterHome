"""
apps.children.views

Full CRUD with search, filtering, and pagination, plus role-based access
control reused from apps.accounts.permissions (Step 5). List/detail views
are readable by any authenticated role; create/update/delete are
restricted to Admin/Case Worker, and Viewers are blocked from mutating
requests even if they somehow reach the URL directly (ViewerReadOnlyMixin
belt-and-suspenders on top of RoleRequiredMixin on the mutating views).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin
from apps.children.forms import ChildForm
from apps.children.models import Child
from apps.core.exports import export_as_csv


def filter_children_queryset(request):
    """
    Shared between ChildListView.get_queryset() and the CSV/Excel export
    views, so "export" always means "export exactly what I'm currently
    looking at" (same search/filters applied), not a separate/inconsistent
    query. Extracting this once is what prevents the two from drifting
    apart as filters are added or changed in the future.
    """
    qs = Child.objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(Q(first_name__icontains=query) | Q(state__icontains=query))

    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)

    gender = request.GET.get("gender")
    if gender:
        qs = qs.filter(gender=gender)

    special_needs = request.GET.get("special_needs")
    if special_needs in ("true", "false"):
        qs = qs.filter(special_needs=(special_needs == "true"))

    is_placed = request.GET.get("is_placed")
    if is_placed in ("true", "false"):
        qs = qs.filter(is_placed=(is_placed == "true"))

    sort = request.GET.get("sort", "-created_at")
    allowed_sorts = {"age", "-age", "created_at", "-created_at", "time_in_care_months", "-time_in_care_months"}
    if sort in allowed_sorts:
        qs = qs.order_by(sort)

    return qs


CHILD_EXPORT_COLUMNS = [
    ("First Name", lambda c: c.first_name),
    ("Age", lambda c: c.age),
    ("Gender", lambda c: c.get_gender_display()),
    ("State", lambda c: c.state),
    ("Special Needs", lambda c: "Yes" if c.special_needs else "No"),
    ("Sibling Group Size", lambda c: c.sibling_group_size),
    ("Behavioral Score", lambda c: c.behavioral_notes_score),
    ("Education Level", lambda c: c.education_level),
    ("Time in Care (months)", lambda c: c.time_in_care_months),
    ("Placed", lambda c: "Yes" if c.is_placed else "No"),
]


class ChildListView(LoginRequiredMixin, ListView):
    model = Child
    template_name = "children/child_list.html"
    context_object_name = "children"
    paginate_by = 20

    def get_queryset(self):
        return filter_children_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["states"] = Child.objects.values_list("state", flat=True).distinct().order_by("state")
        context["query_params"] = self.request.GET.urlencode()
        return context


@login_required
def export_children_csv(request):
    qs = filter_children_queryset(request)
    return export_as_csv(qs, CHILD_EXPORT_COLUMNS, "children_export")


class ChildDetailView(LoginRequiredMixin, DetailView):
    model = Child
    template_name = "children/child_detail.html"
    context_object_name = "child"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["placements"] = self.object.placements.select_related("family").order_by("-created_at")
        context["predictions"] = self.object.predictions.select_related("family").order_by("-created_at")[:10]
        return context


class ChildCreateView(RoleRequiredMixin, LoginRequiredMixin, CreateView):
    model = Child
    form_class = ChildForm
    template_name = "children/child_form.html"
    success_url = reverse_lazy("children:index")
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def form_valid(self, form):
        messages.success(self.request, f"Child record for {form.instance.first_name} created.")
        return super().form_valid(form)


class ChildUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Child
    form_class = ChildForm
    template_name = "children/child_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def get_success_url(self):
        return reverse_lazy("children:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Child record for {form.instance.first_name} updated.")
        return super().form_valid(form)


class ChildDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Child
    template_name = "children/child_confirm_delete.html"
    success_url = reverse_lazy("children:index")
    allowed_roles = (Profile.Role.ADMIN,)  # deletion restricted to Admin only, stricter than create/edit

    def form_valid(self, form):
        messages.success(self.request, "Child record deleted.")
        return super().form_valid(form)
