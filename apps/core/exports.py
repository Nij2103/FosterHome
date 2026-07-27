"""
apps.core.exports

Generic CSV/Excel export helpers shared across every app's list views.
Kept in `core` (Step 2: the shared/cross-cutting app) rather than
duplicated per-app, since the actual export mechanics (write rows, set
response headers) are identical regardless of which model is being
exported — only the column definitions differ per call site.

DESIGN: each caller passes a list of (header_label, value_getter) tuples
rather than raw model field names, so computed/related values (e.g.
`child.get_gender_display()`, `family.available_slots`) export exactly
as displayed in the UI, not as raw DB values.
"""

import csv

from django.http import HttpResponse


def export_as_csv(queryset, columns: list[tuple[str, callable]], filename: str) -> HttpResponse:
    """
    columns: [(header_label, lambda obj: value), ...]
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

    writer = csv.writer(response)
    writer.writerow([label for label, _ in columns])
    for obj in queryset:
        writer.writerow([getter(obj) for _, getter in columns])

    return response

