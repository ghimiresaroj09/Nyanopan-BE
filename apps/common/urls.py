"""Internal endpoints for the external scheduler (see apps.common.cron).

Included under ``/api/v1/internal/`` by ``config.urls``.
"""

from django.urls import path

from .views import CronJobView

urlpatterns = [
    path("cron/<slug:job>/", CronJobView.as_view(), name="internal-cron-job"),
]
