"""Operational endpoints: health probes and the internal cron dispatcher.

Neither belongs to the public catalog API. The probes are unauthenticated on
purpose (the hosting platform and external schedulers must be able to reach
them without credentials); the cron endpoints are guarded by a shared secret —
see :mod:`apps.common.cron`.
"""

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .cron import JOBS, check_cron_secret
from .responses import SuccessEnvelopeMixin


@never_cache
def liveness_check(request):
    """Cheap process-only probe (``/api/health/live/``).

    Deliberately touches no external service. It serves two purposes:

    * the platform's ``healthCheckPath`` while an instance is running, and
    * scheduled keep-alive pings that stop a free instance from spinning down.

    Note the split from :func:`health_check`: this view must never touch the
    database. The platform probes every few seconds, and a database-backed
    probe would keep a scale-to-zero Postgres (Neon) permanently awake,
    burning its monthly free compute allowance for no benefit — Neon resumes
    from a suspend in milliseconds, so there is nothing to keep warm.
    """
    return JsonResponse({"status": "alive"})


@never_cache
def health_check(request):
    """Readiness probe (``/api/health/``): process **and** database.

    Confirms the database answers a trivial query. Returns ``200`` when
    healthy, ``503`` otherwise, so the platform can hold traffic back from a
    broken instance. Point uptime monitors and manual checks here; point
    high-frequency keep-alive pings at :func:`liveness_check` instead.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:  # any failure means "not ready": return 503, never a 500
        return JsonResponse(
            {"status": "unhealthy", "database": "unreachable"}, status=503
        )

    return JsonResponse({"status": "healthy", "database": "ok"})


_CRON_JOB_PARAMETER = OpenApiParameter(
    name="job",
    type=str,
    location=OpenApiParameter.PATH,
    description=(
        "Registered job name: `tokens` (delete expired JWT rows) or "
        "`sessions` (delete expired admin sessions)."
    ),
)


@extend_schema(
    tags=["Internal"],
    summary="Run a scheduled maintenance job",
    description=(
        "Entry point for the external scheduler (cron-job.org). The shared "
        "secret must be sent in the `X-Cron-Secret` header — query parameters "
        "are deliberately not accepted, because access logs record the full "
        "request line and would leak the secret. Answers `503` while no "
        "`CRON_SECRET` is configured (fail closed), `403` on a missing or "
        "wrong secret, and `404` for an unregistered job name. `GET` and "
        "`POST` behave identically so either can be configured in the "
        "scheduler."
    ),
    # No request body: the job name is in the path and the secret in a header.
    request=None,
    parameters=[_CRON_JOB_PARAMETER],
    responses={200: OpenApiTypes.OBJECT},
)
class CronJobView(SuccessEnvelopeMixin, APIView):
    """Run one registered maintenance job."""

    use_status_envelope = True

    def get_success_message(self, request) -> str:
        return f"Cron job '{self.kwargs.get('job', '')}' completed."

    def get(self, request, job):
        return self._run(request, job)

    def post(self, request, job):
        return self._run(request, job)

    def _run(self, request, job):
        check_cron_secret(request)  # 503 if unconfigured, 403 if unauthorized
        handler = JOBS.get(job)
        if handler is None:
            raise NotFound(f"Unknown cron job: {job}.")
        return Response({"job": job, **handler()}, status=status.HTTP_200_OK)
