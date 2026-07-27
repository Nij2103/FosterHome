from django.contrib import admin

from apps.predictions.models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("child", "family", "compatibility_score", "model_name", "model_version", "created_at")
    list_filter = ("model_name", "model_version")
    search_fields = ("child__first_name", "family__family_name")
