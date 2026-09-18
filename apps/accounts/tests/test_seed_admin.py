"""Seeded-admin tests: created on demand, idempotent, skips without config."""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.accounts.signals import seed_admin_user

pytestmark = pytest.mark.django_db

CONFIG = {
    "TESTING": False,
    "ADMIN_SEED_EMAIL": "owner@example.com",
    "ADMIN_SEED_PASSWORD": "Owner-Seed-123",
}


class TestSeedAdmin:
    def test_creates_superuser(self):
        with override_settings(**CONFIG):
            message = seed_admin_user()
        assert "Seeded" in message
        user = get_user_model().objects.get(email="owner@example.com")
        assert user.is_superuser and user.is_staff and user.is_active
        assert user.check_password("Owner-Seed-123")

    def test_idempotent_and_keeps_existing_password(self):
        with override_settings(**CONFIG):
            seed_admin_user()
            user = get_user_model().objects.get(email="owner@example.com")
            user.set_password("changed-later-456")
            user.save()
            message = seed_admin_user()
        assert "already exists" in message
        user.refresh_from_db()
        assert user.check_password("changed-later-456")

    def test_skipped_without_config(self):
        with override_settings(TESTING=False, ADMIN_SEED_EMAIL="", ADMIN_SEED_PASSWORD=""):
            assert seed_admin_user() is None

    def test_skipped_when_testing(self):
        with override_settings(**{**CONFIG, "TESTING": True}):
            assert seed_admin_user() is None
