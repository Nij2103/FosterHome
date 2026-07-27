"""
apps.families.views
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin
from apps.core.exports import export_as_csv
from apps.families.forms import FosterFamilyForm
from apps.families.models import FosterFamily


def filter_families_queryset(request):
    """Shared between FosterFamilyListView and the export views — see
    apps.children.views.filter_children_queryset for the same rationale."""
    qs = FosterFamily.objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(Q(family_name__icontains=query) | Q(state__icontains=query))

    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)

    home_type = request.GET.get("home_type")
    if home_type:
        qs = qs.filter(home_type=home_type)

    accepts_special_needs = request.GET.get("accepts_special_needs")
    if accepts_special_needs in ("true", "false"):
        qs = qs.filter(accepts_special_needs=(accepts_special_needs == "true"))

    available_only = request.GET.get("available_only")
    if available_only == "true":
        qs = qs.filter(current_occupancy__lt=F("capacity"), is_active=True)

    sort = request.GET.get("sort", "-created_at")
    allowed_sorts = {"capacity", "-capacity", "experience_years", "-experience_years", "created_at", "-created_at"}
    if sort in allowed_sorts:
        qs = qs.order_by(sort)

    return qs


FAMILY_EXPORT_COLUMNS = [
    ("Family Name", lambda f: f.family_name),
    ("State", lambda f: f.state),
    ("Capacity", lambda f: f.capacity),
    ("Current Occupancy", lambda f: f.current_occupancy),
    ("Available Slots", lambda f: f.available_slots),
    ("Experience (years)", lambda f: f.experience_years),
    ("Accepts Special Needs", lambda f: "Yes" if f.accepts_special_needs else "No"),
    ("Accepts Sibling Groups", lambda f: "Yes" if f.accepts_sibling_groups else "No"),
    ("Home Type", lambda f: f.get_home_type_display()),
    ("Active", lambda f: "Yes" if f.is_active else "No"),
]


class FosterFamilyListView(LoginRequiredMixin, ListView):
    model = FosterFamily
    template_name = "families/fosterfamily_list.html"
    context_object_name = "families"
    paginate_by = 20

    def get_queryset(self):
        return filter_families_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["states"] = FosterFamily.objects.values_list("state", flat=True).distinct().order_by("state")
        context["query_params"] = self.request.GET.urlencode()
        return context


@login_required
def export_families_csv(request):
    qs = filter_families_queryset(request)
    return export_as_csv(qs, FAMILY_EXPORT_COLUMNS, "families_export")


class FosterFamilyDetailView(LoginRequiredMixin, DetailView):
    model = FosterFamily
    template_name = "families/fosterfamily_detail.html"
    context_object_name = "fosterfamily"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["family"] = self.object
        context["placements"] = self.object.placements.select_related("child").order_by("-created_at")
        return context


class FosterFamilyCreateView(RoleRequiredMixin, LoginRequiredMixin, CreateView):
    model = FosterFamily
    form_class = FosterFamilyForm
    template_name = "families/fosterfamily_form.html"
    success_url = reverse_lazy("families:index")
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def form_valid(self, form):
        messages.success(self.request, f"Foster family {form.instance.family_name} created.")
        return super().form_valid(form)


class FosterFamilyUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = FosterFamily
    form_class = FosterFamilyForm
    template_name = "families/fosterfamily_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def get_success_url(self):
        return reverse_lazy("families:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Foster family {form.instance.family_name} updated.")
        return super().form_valid(form)


class FosterFamilyDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    model = FosterFamily
    template_name = "families/fosterfamily_confirm_delete.html"
    success_url = reverse_lazy("families:index")
    allowed_roles = (Profile.Role.ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, "Foster family deleted.")
        return super().form_valid(form)
