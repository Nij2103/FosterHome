"""
apps.accounts.views
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms import ProfileUpdateForm, RegistrationForm, UserUpdateForm


def register(request):
    if request.user.is_authenticated:
        return redirect("analytics:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after registering — standard,
            # friendlier UX than forcing a second login step.
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("analytics:dashboard")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"profile": request.user.profile})


@login_required
def settings_view(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your settings have been updated.")
            return redirect("accounts:settings")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(
        request,
        "accounts/settings.html",
        {"user_form": user_form, "profile_form": profile_form},
    )
