"""Tests for the deployment health probes.

Two endpoints with deliberately different jobs:

* ``/api/health/live/`` — process only, no database. Used by the platform's
  ``healthCheckPath`` and by scheduled keep-alive pings.
* ``/api/health/`` — process + database readiness.

The split is not cosmetic: the platform probes every few seconds, so a
database-backed probe would keep a scale-to-zero Postgres awake 24/7 and burn
through its monthly free compute allowance.
"""

from django.db import OperationalError


class BrokenConnection:
    """Stands in for a database connection that is refusing queries."""

    def cursor(self):
        raise OperationalError("connection refused")


class TestLivenessCheck:
    def test_alive(self, client):
        response = client.get("/api/health/live/")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_touches_no_database(self, client, db, django_assert_num_queries):
        with django_assert_num_queries(0):
            response = client.get("/api/health/live/")

        assert response.status_code == 200

    def test_still_alive_when_database_is_down(self, client, db, monkeypatch):
        monkeypatch.setattr("apps.common.views.connection", BrokenConnection())

        response = client.get("/api/health/live/")

        assert response.status_code == 200

    def test_probe_is_not_cacheable(self, client):
        response = client.get("/api/health/live/")

        assert "no-cache" in response.headers["Cache-Control"]


class TestHealthCheck:
    def test_healthy_when_database_answers(self, client, db):
        response = client.get("/api/health/")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "database": "ok"}

    def test_unhealthy_when_database_is_down(self, client, db, monkeypatch):
        monkeypatch.setattr("apps.common.views.connection", BrokenConnection())

        response = client.get("/api/health/")

        assert response.status_code == 503
        assert response.json() == {"status": "unhealthy", "database": "unreachable"}

    def test_probe_is_not_cacheable(self, client, db):
        response = client.get("/api/health/")

        assert "no-cache" in response.headers["Cache-Control"]

    def test_probe_needs_no_authentication(self, client, db):
        response = client.get("/api/health/")

        assert response.status_code != 401
