"""
placements.models

A Placement is a real-world (or proposed) decision linking one Child to one
FosterFamily. This is distinct from predictions.Prediction, which stores a
model's *opinion* before any decision is made — see Step 3 design notes for
the full reasoning.

The 'disrupted' status directly encodes this project's problem statement:
a child returning to care after a placement fails. That makes status the
natural label for a future "placement disruption risk" model.
"""

from django.conf import settings
from django.db import models

from apps.children.models import Child
from apps.families.models import FosterFamily


class Placement(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        ACTIVE = "active", "Active"
        DISRUPTED = "disrupted", "Disrupted"
        COMPLETED = "completed", "Completed"

    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="placements",
        help_text="If the child record is deleted, its placement history goes with it.",
    )
    family = models.ForeignKey(
        FosterFamily, on_delete=models.CASCADE, related_name="placements",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROPOSED, db_index=True,
    )
    placed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # keep historical record even if the user account is later removed
        null=True,
        blank=True,
        related_name="placements_recorded",
        help_text="The case worker who recorded this placement.",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    disruption_reason = models.TextField(
        blank=True,
        help_text="Filled in only when status = Disrupted.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.child} -> {self.family} [{self.status}]"
