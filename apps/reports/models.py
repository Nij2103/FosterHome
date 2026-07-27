"""
reports.models

Report stores metadata + parsed text for one scraped document (PDF or HTML
page). ReportStatistic stores individual numeric data points extracted from
a Report, one row per (state, year, metric) — a long/tidy format that maps
directly onto what Pandas groupby and Seaborn plotting expect. A single
report often contains dozens of statistics, so keeping them as separate
rows (rather than dozens of columns on Report) is the normalized design —
see Step 3 notes.
"""

from django.db import models


class Report(models.Model):
    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        HTML = "html", "HTML"

    title = models.CharField(max_length=255)
    source_url = models.URLField(
        help_text="Public government report URL this was scraped from.",
    )
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    raw_file = models.FileField(upload_to="reports/raw/", blank=True, null=True)
    parsed_text = models.TextField(
        blank=True,
        help_text="Cleaned plain-text extraction, used for keyword search.",
    )
    published_year = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scraped_at"]

    def __str__(self):
        return self.title


class ReportStatistic(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="statistics")
    state = models.CharField(max_length=100, db_index=True)
    year = models.PositiveSmallIntegerField(db_index=True)
    metric_name = models.CharField(
        max_length=150,
        help_text="e.g. 'children_in_foster_care', 'successful_placements'.",
    )
    value = models.FloatField()

    class Meta:
        ordering = ["state", "year"]
        indexes = [
            models.Index(fields=["state", "year", "metric_name"]),
        ]

    def __str__(self):
        return f"{self.state} {self.year} - {self.metric_name}: {self.value}"
