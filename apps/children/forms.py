"""
apps.children.forms
"""

from django import forms

from apps.children.models import Child


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = [
            "first_name", "age", "gender", "state", "special_needs",
            "sibling_group_size", "behavioral_notes_score", "education_level",
            "time_in_care_months", "is_placed",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 17}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "special_needs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sibling_group_size": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "behavioral_notes_score": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": 0, "max": 1}),
            "education_level": forms.TextInput(attrs={"class": "form-control"}),
            "time_in_care_months": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "is_placed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_age(self):
        age = self.cleaned_data["age"]
        if not (0 <= age <= 17):
            raise forms.ValidationError("Age must be between 0 and 17 for a child in foster care.")
        return age

    def clean_behavioral_notes_score(self):
        score = self.cleaned_data["behavioral_notes_score"]
        if not (0.0 <= score <= 1.0):
            raise forms.ValidationError("Behavioral notes score must be between 0.0 and 1.0.")
        return score
