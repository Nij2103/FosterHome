"""
predictions.models

Stores the ML pipeline's *output* (a compatibility score) for a given
Child-FosterFamily pair, along with which model produced it. Kept separate
from placements.Placement because a case worker may request predictions for
several candidate families before ever creating a real Placement — folding
these into one table would violate normalization and make model auditing
(which prediction, from which model version, influenced which decision)
much harder to reconstruct later.
"""

from django.conf import settings
from django.db import models

from apps.children.models import Child
from apps.families.models import FosterFamily


class Prediction(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="predictions")
    family = models.ForeignKey(FosterFamily, on_delete=models.CASCADE, related_name="predictions")
    compatibility_score = models.FloatField(
        help_text="Model output in the range 0.0-1.0, higher is more compatible.",
    )
    model_name = models.CharField(
        max_length=100,
        help_text="e.g. 'RandomForestClassifier', 'GradientBoosting'.",
    )
    model_version = models.CharField(
        max_length=20,
        help_text="e.g. 'v1', tied to the artifact filename in ml/models_store/.",
    )
    predicted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="predictions_requested",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    explanation_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="SHAP local feature attribution breakdown and casework risk drivers.",
    )


    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["child", "family"]),
        ]

    def __str__(self):
        return f"{self.child} x {self.family}: {self.compatibility_score:.2f}"

    @property
    def top_risk_drivers(self) -> list[dict]:
        if not self.explanation_data:
            return []
        return self.explanation_data.get("risk_drivers", [])

    @property
    def top_stability_drivers(self) -> list[dict]:
        if not self.explanation_data:
            return []
        return self.explanation_data.get("stability_drivers", [])

    @property
    def summary_explanation_text(self) -> str:
        if not self.explanation_data:
            return "Explainability metrics unavailable for this prediction."
        return self.explanation_data.get("shap_summary_text", "")

