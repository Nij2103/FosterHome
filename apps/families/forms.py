"""
apps.families.forms
"""

from django import forms

from apps.families.models import FosterFamily


class FosterFamilyForm(forms.ModelForm):
    class Meta:
        model = FosterFamily
        fields = [
            "family_name", "state", "capacity", "current_occupancy",
            "experience_years", "accepts_special_needs", "accepts_sibling_groups",
            "home_type", "is_active",
        ]
        widgets = {
            "family_name": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "current_occupancy": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "accepts_special_needs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "accepts_sibling_groups": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "home_type": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        capacity = cleaned.get("capacity")
        occupancy = cleaned.get("current_occupancy")
        if capacity is not None and occupancy is not None and occupancy > capacity:
            raise forms.ValidationError("Current occupancy cannot exceed capacity.")
        return cleaned
