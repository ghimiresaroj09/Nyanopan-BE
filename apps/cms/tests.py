"""CMS tests."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.cms.models import SiteConfiguration


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def site_config():
    config = SiteConfiguration.get_config()
    config.email = "test@example.com"
    config.phone = "+977-1234567890"
    config.whatsapp = "+977-9876543210"
    config.address = "Test Address, Kathmandu"
    config.map_url = "https://maps.google.com/test"
    config.facebook_url = "https://facebook.com/test"
    config.instagram_url = "https://instagram.com/test"
    config.tiktok_url = "https://tiktok.com/@test"
    config.pinterest_url = "https://pinterest.com/test"
    config.save()
    return config


@pytest.mark.django_db
class TestSiteConfigurationPublicAPI:
    """Test public configuration endpoint."""

    def test_get_configuration_no_auth_required(self, api_client, site_config):
        """Public endpoint should not require authentication."""
        url = reverse("cms:configuration-public")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "data" in response.data

    def test_configuration_structure(self, api_client, site_config):
        """Response should have correct structure with nested social object."""
        url = reverse("cms:configuration-public")
        response = api_client.get(url)
        
        data = response.data["data"]
        assert data["email"] == "test@example.com"
        assert data["phone"] == "+977-1234567890"
        assert data["whatsapp"] == "+977-9876543210"
        assert data["address"] == "Test Address, Kathmandu"
        assert data["map_url"] == "https://maps.google.com/test"
        
        # Check nested social object
        assert "social" in data
        assert data["social"]["facebook"] == "https://facebook.com/test"
        assert data["social"]["instagram"] == "https://instagram.com/test"
        assert data["social"]["tiktok"] == "https://tiktok.com/@test"
        assert data["social"]["pinterest"] == "https://pinterest.com/test"

    def test_public_excludes_timestamps(self, api_client, site_config):
        """Public endpoint should not expose timestamps."""
        url = reverse("cms:configuration-public")
        response = api_client.get(url)
        
        data = response.data["data"]
        assert "created_at" not in data
        assert "updated_at" not in data


@pytest.mark.django_db
class TestSiteConfigurationAdminAPI:
    """Test admin configuration endpoint."""

    def test_get_requires_admin(self, api_client, site_config):
        """Admin endpoint should require authentication."""
        url = reverse("cms_admin:configuration-admin")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_includes_all_fields(self, api_client, site_config, admin_user):
        """Admin endpoint should include all fields including timestamps."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:configuration-admin")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        
        # Should include timestamps
        assert "created_at" in data
        assert "updated_at" in data
        assert "id" in data

    def test_update_configuration(self, api_client, site_config, admin_user):
        """Admin should be able to update configuration."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:configuration-admin")
        
        update_data = {
            "email": "updated@example.com",
            "phone": "+977-9999999999",
            "social": {
                "facebook": "https://facebook.com/updated",
                "instagram": "https://instagram.com/updated",
            }
        }
        
        response = api_client.patch(url, update_data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["email"] == "updated@example.com"
        assert data["phone"] == "+977-9999999999"
        assert data["social"]["facebook"] == "https://facebook.com/updated"
        assert data["social"]["instagram"] == "https://instagram.com/updated"


@pytest.mark.django_db
class TestSiteConfigurationModel:
    """Test SiteConfiguration model."""

    def test_singleton_pattern(self):
        """Only one instance should be allowed."""
        config1 = SiteConfiguration.get_config()
        config2 = SiteConfiguration.get_config()
        
        assert config1.pk == config2.pk
        assert SiteConfiguration.objects.count() == 1

    def test_get_config_creates_if_not_exists(self):
        """get_config should create instance if it doesn't exist."""
        SiteConfiguration.objects.all().delete()
        
        config = SiteConfiguration.get_config()
        
        assert config is not None
        assert config.pk is not None
        assert SiteConfiguration.objects.count() == 1
