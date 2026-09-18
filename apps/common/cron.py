"""Scheduled maintenance jobs driven by an external scheduler (cron-job.org).

Why not an in-process scheduler or a Render cron job:

* Render's free web service spins down, so nothing in-process survives to fire
  on time;
* Render cron jobs carry a $1/month minimum and their runs consume the same
  free instance hours as the web service.

So an external scheduler calls the token-guarded endpoints wired up in
``config/urls.py`` (``/api/v1/internal/cron/<job>/``), which dispatch through
the ``JOBS`` registry below.

Security
--------
``CRON_SECRET`` (environment variable) is a shared secret sent in the
``X-Cron-Secret`` header. It is deliberately **not** accepted as a query
parameter: access logs record the full request line, which would write the
secret into the log stream. The endpoints fail closed — with no secret
configured they answer ``503`` and run nothing.

Adding a job
------------
Write a function that does the work and returns a JSON-serialisable summary,
then register it in ``JOBS``. It is immediately reachable at
``/api/v1/internal/cron/<name>/`` for both ``GET`` and ``POST``, and shows up
in the docs under the ``Internal`` tag.
"""

from __future__ import annotations

import hmac
from typing import Callable

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied

#: Header carrying the shared secret (cron-job.org: job editor -> custom headers).
CRON_SECRET_HEADER = "X-Cron-Secret"

#: Shorter values are treated as unset: a guessable secret is worse than none.
MIN_SECRET_LENGTH = 16


class CronDisabled(APIException):
    """No usable ``CRON_SECRET`` configured — refuse to run anything."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = (
        "Cron endpoints are disabled: set CRON_SECRET (at least 16 characters) "
        "to enable them."
    )
    default_code = "cron_disabled"


def cron_secret() -> str:
    return (getattr(settings, "CRON_SECRET", "") or "").strip()


def check_cron_secret(request) -> None:
    """Allow or deny a cron request.

    Raises ``CronDisabled`` (503) when no usable secret is configured and
    ``PermissionDenied`` (403) when the header is missing or wrong. Both raise
    before any job name is resolved, so unauthenticated callers cannot probe
    which jobs exist.
    """
    secret = cron_secret()
    if len(secret) < MIN_SECRET_LENGTH:
        raise CronDisabled()

    provided = request.headers.get(CRON_SECRET_HEADER, "")
    if not provided or not hmac.compare_digest(
        provided.encode("utf-8"), secret.encode("utf-8")
    ):
        raise PermissionDenied("Invalid cron secret.")


def purge_expired_tokens() -> dict:
    """Delete expired outstanding JWT rows (blacklist entries cascade)."""
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    _, deleted = OutstandingToken.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()
    return {
        "expired_tokens": deleted.get("token_blacklist.OutstandingToken", 0),
        "blacklist_entries": deleted.get("token_blacklist.BlacklistedToken", 0),
    }


def purge_expired_sessions() -> dict:
    """Delete expired Django sessions (one row per admin login)."""
    from django.contrib.sessions.models import Session

    deleted, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
    return {"expired_sessions": deleted}


#: Job name -> callable returning a summary dict. Names are URL path segments.
JOBS: dict[str, Callable[[], dict]] = {
    "tokens": purge_expired_tokens,
    "sessions": purge_expired_sessions,
}
