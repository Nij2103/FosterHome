"""
apps.accounts.views
"""

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms import CustomPasswordChangeForm, ProfileUpdateForm, RegistrationForm, UserUpdateForm


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
    recent_predictions = request.user.predictions_requested.select_related("child", "family").order_by("-created_at")[:5]
    my_families = request.user.families_created.filter(is_active=True).order_by("-created_at")
    return render(
        request,
        "accounts/profile.html",
        {
            "profile": request.user.profile,
            "recent_predictions": recent_predictions,
            "my_families": my_families,
        },
    )


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


@login_required
def change_password(request):
    """
    Allows any logged in user (Viewer, Case Worker, Admin) to change their password.
    Requires correct Old Password verification before password update is allowed,
    and enforces that the new password cannot be identical to the old password.
    """
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Your password has been changed successfully!")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Failed to change password. Please check the field errors below.")
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})
