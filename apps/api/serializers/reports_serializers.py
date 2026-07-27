"""
apps.api.serializers.reports_serializers
"""

from rest_framework import serializers

from apps.reports.models import Report, ReportStatistic


class ReportStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStatistic
        fields = ["id", "report", "state", "year", "metric_name", "value"]
        read_only_fields = ["id"]


class ReportSerializer(serializers.ModelSerializer):
    statistics = ReportStatisticSerializer(many=True, read_only=True)
    statistics_count = serializers.IntegerField(source="statistics.count", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "title", "source_url", "file_type", "published_year",
            "scraped_at", "statistics_count", "statistics",
        ]
        read_only_fields = fields  # Reports are only created by the
        # scrape_reports management command (Step 6) — the API exposes
        # them read-only, consistent with the web UI's Report views.
