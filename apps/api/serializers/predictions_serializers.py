"""
apps.api.serializers.predictions_serializers
"""

from rest_framework import serializers

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.predictions.models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source="child.first_name", read_only=True)
    family_name = serializers.CharField(source="family.family_name", read_only=True)
    predicted_by_username = serializers.CharField(source="predicted_by.username", read_only=True, default=None)

    class Meta:
        model = Prediction
        fields = [
            "id", "child", "child_name", "family", "family_name",
            "compatibility_score", "model_name", "model_version",
            "predicted_by", "predicted_by_username", "explanation_data", "created_at",
        ]

        read_only_fields = fields  # Predictions are only ever created via
        # PredictionRequestSerializer below (they're a computed RESULT,
        # not a directly user-editable record) — see feature_engineering.py
        # docstring for the same distinction made on the web-view side.


class PredictionRequestSerializer(serializers.Serializer):
    """
    Input serializer for POST /api/v1/predictions/request/ — takes a
    child + family ID pair, NOT Prediction fields directly, since the
    compatibility_score/model_name are computed by running the actual
    trained model (ml.inference.predict), not supplied by the client.
    """
    child = serializers.PrimaryKeyRelatedField(queryset=Child.objects.all())
    family = serializers.PrimaryKeyRelatedField(queryset=FosterFamily.objects.all())
