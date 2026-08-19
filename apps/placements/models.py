"""
placements.models

Placement decision records linking Child to FosterFamily.
Includes Human-in-the-Loop Override logging to track caseworker overrides
when placing children despite low ML scores or warning flags.
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

    class PlacementType(models.TextChoices):
        EMERGENCY = "emergency", "Emergency"
        SHORT_TERM = "short_term", "Short-Term"
        LONG_TERM = "long_term", "Long-Term"
        RESPITE = "respite", "Respite"

    class Outcome(models.TextChoices):
        COMPLETED_SUCCESSFULLY = "completed_successfully", "Completed Successfully"
        DISRUPTED = "disrupted", "Disrupted"
        CHILD_REUNIFIED = "child_reunified", "Child Reunified"
        ADOPTED = "adopted", "Adopted"
        TRANSFER = "transfer", "Transfer to Another Family"

    # --- CORE ASSIGNMENT ---
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="placements",
        help_text="If the child record is deleted, its placement history goes with it.",
    )
    family = models.ForeignKey(
        FosterFamily, on_delete=models.CASCADE, related_name="placements",
    )

    # Prediction reference (optional — auto-populated when created from a prediction)
    prediction = models.ForeignKey(
        "predictions.Prediction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placements",
        help_text="The ML prediction that informed this placement decision (optional).",
    )
    compatibility_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Compatibility score (0.0-1.0) pulled from the linked prediction.",
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROPOSED, db_index=True,
    )
    placement_type = models.CharField(
        max_length=20,
        choices=PlacementType.choices,
        blank=True,
        default="",
        help_text="Classification of the placement type.",
    )

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True, help_text="Expected end date.")
    actual_end_date = models.DateField(
        null=True, blank=True, help_text="Actual end date (filled on closure)."
    )

    # Staff
    placed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placements_recorded",
        help_text="The case worker who recorded this placement.",
    )
    assigned_caseworker = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Name of the caseworker assigned to oversee this placement.",
    )

    # Notes
    placement_notes = models.TextField(
        blank=True,
        default="",
        help_text="General placement notes and context.",
    )

    # Closure fields
    outcome = models.CharField(
        max_length=50,
        choices=Outcome.choices,
        blank=True,
        default="",
        help_text="Final outcome (completed/disrupted placements only).",
    )
    final_notes = models.TextField(
        blank=True,
        default="",
        help_text="Final case notes recorded at placement closure.",
    )
    disruption_reason = models.TextField(
        blank=True,
        help_text="Filled in only when status = Disrupted.",
    )

    # Human-in-the-Loop Override Logging (preserved)
    is_override = models.BooleanField(
        default=False,
        help_text="Flagged when placement proceeds despite low ML score or safety warnings.",
    )
    override_justification = models.TextField(
        blank=True,
        default="",
        help_text="Mandatory casework justification text provided when overriding ML recommendations.",
    )
    override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_overrides",
    )
    override_timestamp = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.child} -> {self.family} [{self.status}]"

    @property
    def compatibility_percentage(self):
        if self.compatibility_score is not None:
            return round(self.compatibility_score * 100, 1)
        return None


class PlacementOverrideLog(models.Model):
    """
    Dedicated audit log for Human-in-the-Loop Caseworker Overrides.
    """
    placement = models.ForeignKey(
        Placement, on_delete=models.CASCADE, related_name="override_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    justification = models.TextField()
    compatibility_score = models.FloatField(null=True, blank=True)
    reasons = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Override Log #{self.pk} for Placement #{self.placement_id} by {self.user}"
