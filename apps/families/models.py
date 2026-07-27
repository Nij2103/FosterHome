"""
families.models

Like Child, every FosterFamily record here is synthetically generated
(see ml/data/synthetic_generator.py, built later in the ML milestone).
"""

from django.db import models


class FosterFamily(models.Model):
    class HomeType(models.TextChoices):
        URBAN = "urban", "Urban"
        SUBURBAN = "suburban", "Suburban"
        RURAL = "rural", "Rural"

    family_name = models.CharField(
        max_length=150,
        help_text="Synthetic identifier only — never a real family's name.",
    )
    state = models.CharField(max_length=100, db_index=True)
    capacity = models.PositiveSmallIntegerField(
        help_text="Maximum number of children this family can host at once.",
    )
    current_occupancy = models.PositiveSmallIntegerField(default=0)
    experience_years = models.PositiveSmallIntegerField(
        help_text="Years this family has been an active foster placement.",
    )
    accepts_special_needs = models.BooleanField(default=False)
    accepts_sibling_groups = models.BooleanField(default=False)
    home_type = models.CharField(max_length=20, choices=HomeType.choices)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Inactive families are excluded from new placement recommendations.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Foster families"
        indexes = [
            models.Index(fields=["state", "is_active"]),
        ]

    def __str__(self):
        return f"{self.family_name} ({self.state})"

    @property
    def available_slots(self):
        """
        Derived, not stored — see Step 3 normalization notes. Storing this
        would risk going stale whenever current_occupancy changes; computing
        it on access guarantees it is always correct.
        """
        return max(self.capacity - self.current_occupancy, 0)
