"""
apps.api.serializers.children_serializers
"""

from rest_framework import serializers

from apps.children.models import Child


class ChildSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model = Child
        fields = [
            "id", "first_name", "age", "gender", "gender_display", "state",
            "special_needs", "sibling_group_size", "behavioral_notes_score",
            "education_level", "time_in_care_months", "is_placed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_age(self, value):
        if not (0 <= value <= 17):
            raise serializers.ValidationError("Age must be between 0 and 17.")
        return value

    def validate_behavioral_notes_score(self, value):
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError("Must be between 0.0 and 1.0.")
        return value
