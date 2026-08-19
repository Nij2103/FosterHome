"""
apps.predictions.forms
"""

from django import forms

from apps.children.models import Child
from apps.families.models import FosterFamily


class PredictionRequestForm(forms.Form):
    child = forms.ModelChoiceField(
        queryset=Child.objects.all().order_by("first_name"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_child"}),
        empty_label="— Select Child —",
    )
    family = forms.ModelChoiceField(
        queryset=FosterFamily.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_family"}),
        empty_label="— Select Foster Family —",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        family_qs = FosterFamily.objects.filter(is_active=True)

        if user and user.is_authenticated and not user.is_superuser:
            profile = getattr(user, "profile", None)
            if profile and profile.is_viewer:
                family_qs = family_qs.filter(created_by=user)

        self.fields["family"].queryset = family_qs.order_by("family_name")

    def clean(self):
        cleaned_data = super().clean()
        child = cleaned_data.get("child")
        family = cleaned_data.get("family")

        if child and family:
            child_completion = child.profile_completion_score
            family_completion = family.profile_completion_score

            if not child_completion.get("is_complete"):
                self.add_error(
                    "child",
                    f"Child profile must reach 100% completion before running predictions. (Current: {child_completion.get('percentage')}%)"
                )

            if not family_completion.get("is_complete"):
                self.add_error(
                    "family",
                    f"Foster family profile must reach 100% completion before running predictions. (Current: {family_completion.get('percentage')}%)"
                )

        return cleaned_data
