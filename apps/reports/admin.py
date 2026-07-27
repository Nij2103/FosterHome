from django.contrib import admin

from apps.reports.models import Report, ReportStatistic


class ReportStatisticInline(admin.TabularInline):
    model = ReportStatistic
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "file_type", "published_year", "scraped_at")
    list_filter = ("file_type", "published_year")
    search_fields = ("title", "source_url")
    inlines = [ReportStatisticInline]


@admin.register(ReportStatistic)
class ReportStatisticAdmin(admin.ModelAdmin):
    list_display = ("report", "state", "year", "metric_name", "value")
    list_filter = ("state", "year", "metric_name")
