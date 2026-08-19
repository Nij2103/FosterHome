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
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User

from apps.accounts.models import Profile


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com"}))
    organization = forms.CharField(max_length=150, required=False)
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("Username is required.")

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose a different username.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise forms.ValidationError("Email address is required.")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please sign in or use a different email.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
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
        widgets = {
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "9876543210", "maxlength": "15"}),
            "organization": forms.TextInput(attrs={"class": "form-control", "placeholder": "Organization Name"}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if not phone:
            return ""

        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]

        if len(digits) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number (no more, no less).")

        if digits[0] not in ("6", "7", "8", "9"):
            raise forms.ValidationError("Indian phone number must start with 6, 7, 8, or 9.")

        return f"+91-{digits[:5]}-{digits[5:]}"


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Enforces that the new password cannot be identical to the current old password.
    """

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password1 = cleaned_data.get("new_password1")

        if old_password and new_password1 and old_password == new_password1:
            self.add_error("new_password1", "Your new password cannot be the same as your old password.")

        return cleaned_data
