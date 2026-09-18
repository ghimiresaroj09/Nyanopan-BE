"""Tests for the internal cron endpoints (external scheduler entry points).

The security posture matters as much as the jobs: these endpoints fail closed,
never accept the secret in a query string (access logs record the request
line), and authenticate before revealing which jobs exist.
"""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

SECRET = "test-cron-secret-0123456789"
HEADER = "X-Cron-Secret"


@pytest.fixture
def cron_secret(settings):
    settings.CRON_SECRET = SECRET
    return SECRET


@pytest.fixture
def expired_tokens(admin_user):
    """One expired token (blacklisted) plus one live token."""
    now = timezone.now()
    expired = OutstandingToken.objects.create(
        user=admin_user,
        jti=uuid4(),
        token="expired-token",
        created_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
    )
    BlacklistedToken.objects.create(token=expired)
    live = OutstandingToken.objects.create(
        user=admin_user,
        jti=uuid4(),
        token="live-token",
        created_at=now,
        expires_at=now + timedelta(days=1),
    )
    return expired, live


@pytest.fixture
def expired_sessions():
    now = timezone.now()
    expired = Session.objects.create(
        session_key="expired-session", session_data="", expire_date=now - timedelta(days=1)
    )
    live = Session.objects.create(
        session_key="live-session", session_data="", expire_date=now + timedelta(days=1)
    )
    return expired, live


class TestCronAuthentication:
    def test_disabled_when_secret_not_configured(self, client, db, settings):
        settings.CRON_SECRET = ""

        response = client.get("/api/v1/internal/cron/tokens/")

        assert response.status_code == 503
        assert response.json()["message"] == "Service unavailable."
        assert "CRON_SECRET" in response.json()["errors"]["detail"]

    def test_disabled_when_secret_too_short(self, client, db, settings):
        settings.CRON_SECRET = "short"

        response = client.get("/api/v1/internal/cron/tokens/")

        assert response.status_code == 503

    def test_missing_header_rejected(self, client, db, cron_secret):
        response = client.get("/api/v1/internal/cron/tokens/")

        assert response.status_code == 403
        assert response.json()["errors"]["detail"] == "Invalid cron secret."

    def test_wrong_secret_rejected(self, client, db, cron_secret):
        response = client.get(
            "/api/v1/internal/cron/tokens/", headers={HEADER: "not-the-secret-at-all"}
        )

        assert response.status_code == 403

    def test_secret_in_query_string_is_not_accepted(self, client, db, cron_secret):
        """The secret must never travel in the URL: logs record the request line."""
        response = client.get(f"/api/v1/internal/cron/tokens/?secret={SECRET}")

        assert response.status_code == 403

    def test_authentication_precedes_job_lookup(self, client, db, cron_secret):
        """An unauthenticated caller must not learn which jobs exist."""
        response = client.get("/api/v1/internal/cron/does-not-exist/")

        assert response.status_code == 403

    def test_staff_jwt_is_not_accepted(self, admin_client, db, cron_secret):
        """A normal admin token is not a cron credential."""
        response = admin_client.get("/api/v1/internal/cron/tokens/")

        assert response.status_code == 403


class TestCronDispatch:
    def test_get_runs_job_with_status_envelope(self, client, db, cron_secret, expired_tokens):
        response = client.get("/api/v1/internal/cron/tokens/", headers={HEADER: SECRET})

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["statusCode"] == 200
        assert payload["message"] == "Cron job 'tokens' completed."
        assert payload["data"] == {
            "job": "tokens",
            "expired_tokens": 1,
            "blacklist_entries": 1,
        }

    def test_post_behaves_identically(self, client, db, cron_secret):
        """cron-job.org may be configured with either method."""
        response = client.post("/api/v1/internal/cron/sessions/", headers={HEADER: SECRET})

        assert response.status_code == 200
        assert response.json()["data"]["job"] == "sessions"

    def test_unknown_job_returns_404(self, client, db, cron_secret):
        response = client.get("/api/v1/internal/cron/nope/", headers={HEADER: SECRET})

        assert response.status_code == 404
        assert response.json()["errors"]["detail"] == "Unknown cron job: nope."


class TestTokenCleanupJob:
    def test_deletes_expired_and_keeps_live(self, client, db, cron_secret, expired_tokens):
        expired, live = expired_tokens

        client.get("/api/v1/internal/cron/tokens/", headers={HEADER: SECRET})

        assert not OutstandingToken.objects.filter(pk=expired.pk).exists()
        assert OutstandingToken.objects.filter(pk=live.pk).exists()
        # The blacklist row cascades with its outstanding token.
        assert BlacklistedToken.objects.count() == 0

    def test_is_idempotent(self, client, db, cron_secret, expired_tokens):
        first = client.get("/api/v1/internal/cron/tokens/", headers={HEADER: SECRET})
        second = client.get("/api/v1/internal/cron/tokens/", headers={HEADER: SECRET})

        assert first.json()["data"]["expired_tokens"] == 1
        assert second.json()["data"]["expired_tokens"] == 0


class TestSessionCleanupJob:
    def test_deletes_expired_and_keeps_live(self, client, db, cron_secret, expired_sessions):
        expired, live = expired_sessions

        response = client.get("/api/v1/internal/cron/sessions/", headers={HEADER: SECRET})

        assert response.json()["data"]["expired_sessions"] == 1
        assert not Session.objects.filter(pk=expired.pk).exists()
        assert Session.objects.filter(pk=live.pk).exists()


class TestJobRegistry:
    def test_registry_is_non_empty_and_callable(self):
        from apps.common.cron import JOBS

        assert JOBS
        for name, handler in JOBS.items():
            assert name.islower()
            assert callable(handler)
