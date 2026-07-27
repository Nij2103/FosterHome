"""
accounts.models

Extends Django's built-in User model via a one-to-one Profile rather than
writing a fully custom user model. This is a deliberate design decision:

WHY NOT A CUSTOM USER MODEL?
Django supports swapping AUTH_USER_MODEL entirely, but doing so adds real
complexity (every migration and third-party app must be aware of it) for
no benefit here — we only need a couple of extra fields (role, phone,
organization). Extending via OneToOneField gives us that with none of the
downside, and it is the officially documented "simple" extension pattern.
"""

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """One row per Django User, carrying the fields Django's User doesn't have."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CASEWORKER = "caseworker", "Case Worker"
        VIEWER = "viewer", "Viewer"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="The Django auth user this profile belongs to.",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        db_index=True,  # frequently filtered on for permission checks
        help_text="Drives both UI rendering and DRF permission checks.",
    )
    phone_number = models.CharField(max_length=15, blank=True)
    organization = models.CharField(
        max_length=150,
        blank=True,
        help_text="e.g. the NGO or government department the user represents.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_caseworker(self):
        return self.role == self.Role.CASEWORKER

    @property
    def is_viewer(self):
        return self.role == self.Role.VIEWER
