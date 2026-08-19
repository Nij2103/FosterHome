"""
apps.families.views
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin
from apps.families.forms import FosterFamilyForm
from apps.families.models import FosterFamily


def filter_families_queryset(request):
    qs = FosterFamily.objects.all()
    if request.user.is_authenticated and not request.user.is_superuser:
        profile = getattr(request.user, "profile", None)
        if profile and profile.is_viewer:
            qs = qs.filter(created_by=request.user)

    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(
            Q(family_name__icontains=query) |
            Q(primary_applicant_name__icontains=query) |
            Q(state__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(licensing_worker_name__icontains=query) |
            Q(identity_doc_number__icontains=query)
        )

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


class FosterFamilyListView(LoginRequiredMixin, ListView):
    model = FosterFamily
    template_name = "families/fosterfamily_list.html"
    context_object_name = "families"
    paginate_by = 20

    def get_queryset(self):
        return filter_families_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context["states"] = qs.values_list("state", flat=True).distinct().order_by("state")
        context["query_params"] = self.request.GET.urlencode()
        return context


class FosterFamilyDetailView(LoginRequiredMixin, DetailView):
    model = FosterFamily
    template_name = "families/fosterfamily_detail.html"
    context_object_name = "fosterfamily"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            profile = getattr(self.request.user, "profile", None)
            if profile and profile.is_viewer:
                qs = qs.filter(created_by=self.request.user)
        return qs

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
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER, Profile.Role.VIEWER)

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, f"Foster family {form.instance.family_name} created.")
        return super().form_valid(form)


class FosterFamilyUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = FosterFamily
    form_class = FosterFamilyForm
    template_name = "families/fosterfamily_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER, Profile.Role.VIEWER)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        obj = self.get_object()
        if not request.user.is_superuser:
            profile = getattr(request.user, "profile", None)
            if profile and profile.is_viewer and obj.created_by != request.user:
                messages.error(request, "Viewers can only edit foster families created by themselves.")
                raise PermissionDenied("You can only edit foster families created by your account.")

        return super().dispatch(request, *args, **kwargs)

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
