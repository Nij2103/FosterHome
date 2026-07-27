"""
apps.accounts.forms

WHY PUBLIC REGISTRATION HARDCODES THE 'VIEWER' ROLE:
Allowing public registration to select 'Case Worker' or 'Admin' would enable
unauthorized users to grant themselves mutation or administrative access to sensitive
child welfare data — a critical privilege escalation security vulnerability. All public
self-registrations strictly default to Viewer access. Role promotion to Case Worker or
Admin is granted exclusively by an Admin through the Django admin panel.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from apps.accounts.models import Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    organization = forms.CharField(max_length=150, required=False)
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ["username", "email"]

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = Profile.Role.VIEWER
            profile.organization = self.cleaned_data.get("organization", "")
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.save()
        return user



class ProfileUpdateForm(forms.ModelForm):
    """Used on the Settings page — deliberately excludes `role` (see above)."""

    class Meta:
        model = Profile
        fields = ["phone_number", "organization"]


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
