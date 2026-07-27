"""
apps.api.docs_views

A hand-written documentation page rather than an auto-generated schema
(drf-spectacular/drf-yasg) — deliberate scope choice for this project:
DRF's own browsable API (visit any endpoint in a browser while logged in)
already provides interactive, accurate, auto-generated documentation for
every field and method. This page adds the plain-English "what is this
resource for and how do the pieces fit together" context that a raw
schema doesn't convey — the two are complementary, not redundant.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

ENDPOINTS = [
    {
        "resource": "Children", "base_url": "/api/v1/children/",
        "methods": "GET (list/retrieve), POST, PUT, PATCH (Admin/Case Worker), DELETE (Admin only)",
        "filters": "?state=&gender=&special_needs=&is_placed=&search=&ordering=",
        "notes": "Search matches first_name/state. Ordering supports age, created_at, time_in_care_months (prefix with - for descending).",
    },
    {
        "resource": "Foster Families", "base_url": "/api/v1/families/",
        "methods": "GET (list/retrieve), POST, PUT, PATCH (Admin/Case Worker), DELETE (Admin only)",
        "filters": "?state=&home_type=&accepts_special_needs=&is_active=&search=&ordering=",
        "notes": "current_occupancy cannot exceed capacity — enforced by the serializer.",
    },
    {
        "resource": "Placements", "base_url": "/api/v1/placements/",
        "methods": "GET (list/retrieve), POST, PUT, PATCH (Admin/Case Worker), DELETE (Admin only)",
        "filters": "?status=&child=&family=&ordering=",
        "notes": "disruption_reason is required when status='disrupted'.",
    },
    {
        "resource": "Predictions", "base_url": "/api/v1/predictions/",
        "methods": "GET (list/retrieve) — read-only for direct creation.",
        "filters": "?child=&family=&model_name=",
        "notes": "To CREATE a prediction, POST to /api/v1/predictions/request_prediction/ "
                 "with {\"child\": <id>, \"family\": <id>} — this runs the actual trained "
                 "model from ml/models_store/, it does not accept a client-supplied score.",
    },
    {
        "resource": "Reports", "base_url": "/api/v1/reports/",
        "methods": "GET (list/retrieve) — read-only.",
        "filters": "?file_type=&published_year=&search=",
        "notes": "Populated by the scrape_reports management command (Step 6). Includes nested statistics.",
    },
    {
        "resource": "Dashboard Stats", "base_url": "/api/v1/dashboard-stats/",
        "methods": "GET",
        "filters": "—",
        "notes": "Same aggregate numbers shown on the web dashboard.",
    },
]


@login_required
def api_docs(request):
    return render(request, "api/docs.html", {"endpoints": ENDPOINTS})
