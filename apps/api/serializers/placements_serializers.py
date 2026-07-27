"""
apps.api.serializers.placements_serializers
"""

from rest_framework import serializers

from apps.placements.models import Placement


class PlacementSerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source="child.first_name", read_only=True)
    family_name = serializers.CharField(source="family.family_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    placed_by_username = serializers.CharField(source="placed_by.username", read_only=True, default=None)

    class Meta:
        model = Placement
        fields = [
            "id", "child", "child_name", "family", "family_name",
            "status", "status_display", "placed_by", "placed_by_username",
            "start_date", "end_date", "disruption_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "placed_by", "created_at", "updated_at"]

    def validate(self, data):
        status = data.get("status", getattr(self.instance, "status", None))
        reason = data.get("disruption_reason", getattr(self.instance, "disruption_reason", ""))
        if status == Placement.Status.DISRUPTED and not reason:
            raise serializers.ValidationError(
                "disruption_reason is required when status is 'disrupted'."
            )
        return data
