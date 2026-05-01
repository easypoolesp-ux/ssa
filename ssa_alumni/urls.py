# =============================================================================
# SSA Alumni — Root URL Configuration
# Responsibility: Route incoming requests to the correct app.
#                 Health check at / prevents Cloud Run 404.
# =============================================================================

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health_check(request):
    """Minimal liveness probe for Cloud Run and load balancers."""
    return JsonResponse({"status": "ok", "service": "ssa-alumni-backend"})


urlpatterns = [
    # ── Health / root ──────────────────────────────────────────────────────
    path("", health_check, name="health-check"),

    # ── Django Admin ──────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── API v1 ─────────────────────────────────────────────────────────────
    path("api/v1/alumni/", include("alumni.urls")),

    # ── OpenAPI Schema + Docs ─────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),
]
