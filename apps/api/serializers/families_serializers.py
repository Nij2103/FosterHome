"""
apps.api.serializers.families_serializers
"""

from rest_framework import serializers

from apps.families.models import FosterFamily


class FosterFamilySerializer(serializers.ModelSerializer):
    home_type_display = serializers.CharField(source="get_home_type_display", read_only=True)
    available_slots = serializers.IntegerField(read_only=True)

    class Meta:
        model = FosterFamily
        fields = [
            "id", "family_name", "state", "capacity", "current_occupancy",
            "available_slots", "experience_years", "accepts_special_needs",
            "accepts_sibling_groups", "home_type", "home_type_display",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        capacity = data.get("capacity", getattr(self.instance, "capacity", None))
        occupancy = data.get("current_occupancy", getattr(self.instance, "current_occupancy", None))
        if capacity is not None and occupancy is not None and occupancy > capacity:
            raise serializers.ValidationError("current_occupancy cannot exceed capacity.")
        return data
