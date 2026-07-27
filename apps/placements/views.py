"""
apps.placements.views
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import Profile
from apps.accounts.permissions import RoleRequiredMixin
from apps.core.exports import export_as_csv
from apps.placements.forms import PlacementForm
from apps.placements.models import Placement


def filter_placements_queryset(request):
    qs = Placement.objects.select_related("child", "family", "placed_by").order_by("-created_at")
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    return qs


PLACEMENT_EXPORT_COLUMNS = [
    ("Child", lambda p: p.child.first_name),
    ("Family", lambda p: p.family.family_name),
    ("Status", lambda p: p.get_status_display()),
    ("Start Date", lambda p: p.start_date),
    ("End Date", lambda p: p.end_date),
    ("Disruption Reason", lambda p: p.disruption_reason),
    ("Recorded By", lambda p: p.placed_by.username if p.placed_by else ""),
    ("Created", lambda p: p.created_at.strftime("%Y-%m-%d")),
]


class PlacementListView(LoginRequiredMixin, ListView):
    model = Placement
    template_name = "placements/placement_list.html"
    context_object_name = "placements"
    paginate_by = 20

    def get_queryset(self):
        return filter_placements_queryset(self.request)


@login_required
def export_placements_csv(request):
    qs = filter_placements_queryset(request)
    return export_as_csv(qs, PLACEMENT_EXPORT_COLUMNS, "placements_export")



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

    def form_valid(self, form):
        form.instance.placed_by = self.request.user
        messages.success(self.request, "Placement recorded.")
        return super().form_valid(form)


class PlacementUpdateView(RoleRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Placement
    form_class = PlacementForm
    template_name = "placements/placement_form.html"
    allowed_roles = (Profile.Role.ADMIN, Profile.Role.CASEWORKER)

    def get_success_url(self):
        return reverse_lazy("placements:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Placement updated.")
        return super().form_valid(form)


class PlacementDeleteView(RoleRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Placement
    template_name = "placements/placement_confirm_delete.html"
    success_url = reverse_lazy("placements:index")
    allowed_roles = (Profile.Role.ADMIN,)

    def form_valid(self, form):
        messages.success(self.request, "Placement deleted.")
        return super().form_valid(form)
