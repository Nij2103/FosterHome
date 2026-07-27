"""
apps.predictions.forms
"""

from django import forms

from apps.children.models import Child
from apps.families.models import FosterFamily


class PredictionRequestForm(forms.Form):
    child = forms.ModelChoiceField(
        queryset=Child.objects.all().order_by("first_name"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    family = forms.ModelChoiceField(
        queryset=FosterFamily.objects.filter(is_active=True).order_by("family_name"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
