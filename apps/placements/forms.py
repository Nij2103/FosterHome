"""
apps.placements.forms
"""

from django import forms

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement


class PlacementForm(forms.ModelForm):
    child = forms.ModelChoiceField(queryset=Child.objects.all().order_by("first_name"), widget=forms.Select(attrs={"class": "form-select"}))
    family = forms.ModelChoiceField(queryset=FosterFamily.objects.filter(is_active=True).order_by("family_name"), widget=forms.Select(attrs={"class": "form-select"}))

    class Meta:
        model = Placement
        fields = ["child", "family", "status", "start_date", "end_date", "disruption_reason"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "disruption_reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        reason = cleaned.get("disruption_reason")
        if status == Placement.Status.DISRUPTED and not reason:
            raise forms.ValidationError("Please provide a disruption reason when marking a placement as disrupted.")
        return cleaned
