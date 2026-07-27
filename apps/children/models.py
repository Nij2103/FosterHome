"""
children.models

IMPORTANT DATA ETHICS NOTE (see project Step 1 planning):
Every Child record in this system is SYNTHETIC. No real child's identity,
history, or welfare record is ever stored here. Fields are designed to be
ML-ready (numeric/categorical) so they can feed directly into the
scikit-learn pipeline in ml/training/ without further transformation of
their basic types — this is a schema decision made with the downstream
data science pipeline in mind, not just data storage.
"""

from django.db import models


class Child(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    first_name = models.CharField(
        max_length=100,
        help_text="Synthetic identifier only — never a real child's name.",
    )
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    state = models.CharField(max_length=100, db_index=True)
    special_needs = models.BooleanField(default=False)
    sibling_group_size = models.PositiveSmallIntegerField(
        default=1,
        help_text="1 means the child has no siblings needing joint placement.",
    )
    sibling_group_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Identifier grouping siblings together for joint placement.",
    )

    behavioral_notes_score = models.FloatField(
        help_text="Synthetic 0.0-1.0 severity index used as an ML feature.",
    )
    education_level = models.CharField(max_length=50)
    time_in_care_months = models.PositiveIntegerField(
        help_text="How long the child has been in the care system so far.",
    )
    is_placed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state", "is_placed"]),
        ]

    def __str__(self):
        return f"{self.first_name} ({self.age}, {self.state})"
