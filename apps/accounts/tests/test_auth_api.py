"""Admin authentication tests: login, refresh, logout, password change, me."""

import uuid

import pytest

from conftest import status_data, success_data

pytestmark = pytest.mark.django_db


class TestAdminAuth:
    def test_login_success(self, api_client, admin_user):
        response = api_client.post(
            "/api/v1/admin/auth/login/",
            {"email": "admin@example.com", "password": "admin-pass-123"},
            format="json",
        )
        data = success_data(response)
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "admin@example.com"
        assert "password" not in data["user"]
        uuid.UUID(str(data["user"]["id"]))

        # The token grants access to admin endpoints.
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        assert status_data(api_client.get("/api/v1/admin/products/"))["count"] == 0

    def test_login_requires_email_field(self, api_client, admin_user):
        response = api_client.post(
            "/api/v1/admin/auth/login/",
            {"username": "admin@example.com", "password": "admin-pass-123"},
            format="json",
        )
        assert response.status_code == 400

    def test_login_wrong_password(self, api_client, admin_user):
        response = api_client.post(
            "/api/v1/admin/auth/login/",
            {"email": "admin@example.com", "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401
        assert response.data["success"] is False

    def test_login_non_staff_denied(self, api_client, plain_user):
        response = api_client.post(
            "/api/v1/admin/auth/login/",
            {"email": "bob@example.com", "password": "bob-pass-123"},
            format="json",
        )
        assert response.status_code == 401

    def test_refresh(self, api_client, admin_user):
        login = success_data(
            api_client.post(
                "/api/v1/admin/auth/login/",
                {"email": "admin@example.com", "password": "admin-pass-123"},
                format="json",
            )
        )
        data = success_data(
            api_client.post(
                "/api/v1/admin/auth/refresh/",
                {"refresh": login["refresh"]},
                format="json",
            )
        )
        assert "access" in data

    def test_logout_blacklists_refresh_token(self, api_client, admin_user):
        login = success_data(
            api_client.post(
                "/api/v1/admin/auth/login/",
                {"email": "admin@example.com", "password": "admin-pass-123"},
                format="json",
            )
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")
        success_data(
            api_client.post(
                "/api/v1/admin/auth/logout/",
                {"refresh": login["refresh"]},
                format="json",
            )
        )
        # Refreshing with a blacklisted token now fails.
        refresh = api_client.post(
            "/api/v1/admin/auth/refresh/",
            {"refresh": login["refresh"]},
            format="json",
        )
        assert refresh.status_code == 401

    def test_me(self, admin_client, api_client):
        data = success_data(admin_client.get("/api/v1/admin/auth/me/"))
        assert data["email"] == "admin@example.com"
        assert api_client.get("/api/v1/admin/auth/me/").status_code == 401

    def test_change_password(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        bad = api_client.post(
            "/api/v1/admin/auth/change-password/",
            {"old_password": "wrong", "new_password": "brand-new-pass-456"},
            format="json",
        )
        assert bad.status_code == 400
        success_data(
            api_client.post(
                "/api/v1/admin/auth/change-password/",
                {"old_password": "admin-pass-123", "new_password": "brand-new-pass-456"},
                format="json",
            )
        )
        # Old password stops working, new one works.
        api_client.force_authenticate(user=None)
        assert (
            api_client.post(
                "/api/v1/admin/auth/login/",
                {"email": "admin@example.com", "password": "admin-pass-123"},
                format="json",
            ).status_code
            == 401
        )
        assert (
            success_data(
                api_client.post(
                    "/api/v1/admin/auth/login/",
                    {"email": "admin@example.com", "password": "brand-new-pass-456"},
                    format="json",
                )
            )["user"]["email"]
            == "admin@example.com"
        )
