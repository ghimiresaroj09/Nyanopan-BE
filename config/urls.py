"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.common.views import health_check, liveness_check

urlpatterns = [
    # Liveness probe: process only, no database. Platform health checks and
    # scheduled keep-alive pings target this one.
    path("api/health/live/", liveness_check, name="health-live"),
    # Readiness probe: process + database. For uptime monitors and manual checks.
    path("api/health/", health_check, name="health"),
    path("admin/", admin.site.urls),
    # OpenAPI schema + documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Versioned API
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/admin/", include("apps.catalog.urls_admin")),
    path("api/v1/admin/auth/", include("apps.accounts.urls")),
    # Token-guarded jobs called by the external scheduler (cron-job.org).
    path("api/v1/internal/", include("apps.common.urls")),
]

if settings.DEBUG:
    # Serve filesystem-fallback uploads during local development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
