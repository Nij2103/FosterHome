"""
apps.placements.forms
"""

from django import forms
from django.db.models import Count, Q, F

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement


CLOSURE_STATUSES = (Placement.Status.COMPLETED, Placement.Status.DISRUPTED)


class PlacementForm(forms.ModelForm):
    """
    Three-section placement form:
      Section 1 – Assignment (child, family, prediction ref, status, dates)
      Section 2 – Details (type, caseworker, notes)
      Section 3 – Closure (actual end date, outcome, final notes) — conditional
    """

    child = forms.ModelChoiceField(
        queryset=Child.objects.all().order_by("first_name"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_child"}),
        empty_label="— Select Child —",
    )
    family = forms.ModelChoiceField(
        queryset=FosterFamily.objects.filter(is_active=True).order_by("family_name"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_family"}),
        empty_label="— Select Foster Family —",
    )

    class Meta:
        model = Placement
        fields = [
            # Section 1
            "child", "family", "prediction", "compatibility_score",
            "status", "start_date", "end_date",
            # Section 2
            "placement_type", "assigned_caseworker", "placement_notes",
            # Section 3 (closure)
            "actual_end_date", "outcome", "final_notes",
        ]
        widgets = {
            "prediction": forms.Select(attrs={"class": "form-select"}),
            "compatibility_score": forms.NumberInput(
                attrs={"class": "form-control", "readonly": "readonly",
                       "step": "0.01", "min": "0", "max": "1"}
            ),
            "status": forms.Select(attrs={"class": "form-select", "id": "id_status"}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "placement_type": forms.Select(attrs={"class": "form-select"}),
            "assigned_caseworker": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Full name of assigned caseworker"}
            ),
            "placement_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3,
                       "placeholder": "Optional general notes about this placement…"}
            ),
            "actual_end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "outcome": forms.Select(attrs={"class": "form-select"}),
            "final_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3,
                       "placeholder": "Final case notes at closure…"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Exclude children who currently have an ACTIVE placement
        active_placements = Placement.objects.filter(status=Placement.Status.ACTIVE)
        if self.instance and self.instance.pk:
            active_placements = active_placements.exclude(pk=self.instance.pk)
        active_child_ids = active_placements.values_list("child_id", flat=True)
        self.fields["child"].queryset = Child.objects.exclude(id__in=active_child_ids).order_by("first_name")

        # 2. Exclude foster families that are at full capacity
        family_qs = FosterFamily.objects.filter(is_active=True)
        if user and user.is_authenticated and not user.is_superuser:
            profile = getattr(user, "profile", None)
            if profile and profile.is_viewer:
                family_qs = family_qs.filter(created_by=user)

        # Count active placements per family (excluding the current instance if editing)
        exclude_placement_filter = Q()
        if self.instance and self.instance.pk:
            exclude_placement_filter = ~Q(placements__pk=self.instance.pk)

        full_family_ids = FosterFamily.objects.annotate(
            active_count=Count(
                "placements",
                filter=Q(placements__status=Placement.Status.ACTIVE) & exclude_placement_filter
            )
        ).filter(active_count__gte=F("capacity")).values_list("id", flat=True)

        self.fields["family"].queryset = family_qs.exclude(id__in=full_family_ids).order_by("family_name")

        # Prediction queryset
        from apps.predictions.models import Prediction
        self.fields["prediction"].queryset = Prediction.objects.select_related(
            "child", "family"
        ).order_by("-created_at")
        self.fields["prediction"].required = False
        self.fields["prediction"].empty_label = "— None (no prediction reference) —"
        self.fields["prediction"].widget.attrs["class"] = "form-select"

        self.fields["compatibility_score"].required = False

        # 3. Status choices: On creation, only Proposed and Active are selectable (Completed & Disrupted are end states allowed only during edit)
        if not (self.instance and self.instance.pk):
            self.fields["status"].choices = [
                (Placement.Status.PROPOSED, Placement.Status.PROPOSED.label),
                (Placement.Status.ACTIVE, Placement.Status.ACTIVE.label),
            ]

        # Closure fields: not required at form level — validated conditionally
        self.fields["actual_end_date"].required = False
        self.fields["outcome"].required = False
        self.fields["outcome"].empty_label = "— Select Outcome —"
        self.fields["final_notes"].required = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        family = cleaned.get("family")

        # Auto-populate compatibility_score from linked prediction if blank
        prediction = cleaned.get("prediction")
        if prediction and not cleaned.get("compatibility_score"):
            cleaned["compatibility_score"] = prediction.compatibility_score

        # Family Capacity check: prevent assigning placement if family has reached full capacity
        if family and status == Placement.Status.ACTIVE:
            active_placements = Placement.objects.filter(
                family=family,
                status=Placement.Status.ACTIVE
            )
            if self.instance and self.instance.pk:
                active_placements = active_placements.exclude(pk=self.instance.pk)

            if active_placements.count() >= family.capacity:
                self.add_error(
                    "family",
                    f"Foster family '{family.family_name}' has reached its maximum capacity of {family.capacity} active placement(s).",
                )

        # Expected End Date must be strictly after Start Date
        start_date = cleaned.get("start_date")
        end_date = cleaned.get("end_date")
        if start_date and end_date:
            if end_date <= start_date:
                self.add_error(
                    "end_date",
                    "Expected End Date must be after the Placement Start Date.",
                )

        return cleaned
