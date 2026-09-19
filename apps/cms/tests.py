"""CMS tests."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.cms.models import Policy, PolicyType, SiteConfiguration


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def site_config():
    config = SiteConfiguration.get_config()
    config.company_intro = "Test Company Introduction"
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
        assert data["company_intro"] == "Test Company Introduction"
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



# ============================================================================
# Policy Tests
# ============================================================================

@pytest.fixture
def shipping_policy():
    return Policy.objects.create(
        type=PolicyType.SHIPPING,
        title="Shipping Policy",
        content="<h2>Shipping Policy</h2><p>We ship within 3-5 business days.</p>",
        is_active=True,
    )


@pytest.fixture
def privacy_policy():
    return Policy.objects.create(
        type=PolicyType.PRIVACY_POLICY,
        title="Privacy Policy",
        content="<h2>Privacy Policy</h2><p>We respect your privacy.</p>",
        is_active=True,
    )


@pytest.fixture
def inactive_policy():
    return Policy.objects.create(
        type=PolicyType.TERMS_CONDITIONS,
        title="Terms and Conditions",
        content="<h2>Terms</h2><p>Terms content.</p>",
        is_active=False,
    )


@pytest.mark.django_db
class TestPolicyPublicAPI:
    """Test public policy endpoints."""

    def test_list_policies_no_auth_required(self, api_client, shipping_policy):
        """Public endpoint should not require authentication."""
        url = reverse("cms:policy-list")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_list_only_active_policies(self, api_client, shipping_policy, privacy_policy, inactive_policy):
        """Public endpoint should only return active policies."""
        url = reverse("cms:policy-list")
        response = api_client.get(url)
        
        data = response.data["data"]["results"]  # Get results from paginated response
        assert len(data) == 2  # Only active policies
        
        types = [p['type'] for p in data]
        assert PolicyType.SHIPPING in types
        assert PolicyType.PRIVACY_POLICY in types
        assert PolicyType.TERMS_CONDITIONS not in types

    def test_retrieve_policy(self, api_client, shipping_policy):
        """Should retrieve a single policy by ID."""
        url = reverse("cms:policy-detail", kwargs={"pk": shipping_policy.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["type"] == PolicyType.SHIPPING
        assert data["title"] == "Shipping Policy"
        assert "<h2>Shipping Policy</h2>" in data["content"]

    def test_filter_by_type(self, api_client, shipping_policy, privacy_policy):
        """Should filter policies by type."""
        url = reverse("cms:policy-list")
        response = api_client.get(url, {"type": PolicyType.SHIPPING})
        
        data = response.data["data"]["results"]  # Get results from paginated response
        assert len(data) == 1
        assert data[0]["type"] == PolicyType.SHIPPING

    def test_policy_includes_type_display(self, api_client, shipping_policy):
        """Response should include human-readable type display."""
        url = reverse("cms:policy-detail", kwargs={"pk": shipping_policy.id})
        response = api_client.get(url)
        
        data = response.data["data"]
        assert "type_display" in data
        assert data["type_display"] == "Shipping"

    def test_public_excludes_sensitive_fields(self, api_client, shipping_policy):
        """Public endpoint should not expose sensitive fields."""
        url = reverse("cms:policy-detail", kwargs={"pk": shipping_policy.id})
        response = api_client.get(url)
        
        data = response.data["data"]
        assert "is_active" not in data
        assert "created_at" not in data
        assert "updated_at" not in data


@pytest.mark.django_db
class TestPolicyAdminAPI:
    """Test admin policy endpoints."""

    def test_list_requires_admin(self, api_client):
        """Admin endpoint should require authentication."""
        url = reverse("cms_admin:policy-admin-list")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_sees_all_policies(self, api_client, admin_user, shipping_policy, inactive_policy):
        """Admin should see both active and inactive policies."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-list")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]["results"]  # Get results from paginated response
        assert len(data) == 2

    def test_admin_includes_all_fields(self, api_client, admin_user, shipping_policy):
        """Admin endpoint should include all fields."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-detail", kwargs={"pk": shipping_policy.id})
        response = api_client.get(url)
        
        data = response.data["data"]
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_policy(self, api_client, admin_user):
        """Admin should be able to create policies."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-list")
        
        policy_data = {
            "type": PolicyType.EXCHANGES_RETURNS,
            "title": "Exchanges & Returns",
            "content": "<h2>Returns</h2><p>30-day return policy.</p>",
            "is_active": True,
        }
        
        response = api_client.post(url, policy_data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Policy.objects.filter(type=PolicyType.EXCHANGES_RETURNS).exists()

    def test_update_policy(self, api_client, admin_user, shipping_policy):
        """Admin should be able to update policies."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-detail", kwargs={"pk": shipping_policy.id})
        
        update_data = {
            "title": "Updated Shipping Policy",
            "content": "<h2>Updated</h2><p>New shipping information.</p>",
        }
        
        response = api_client.patch(url, update_data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        shipping_policy.refresh_from_db()
        assert shipping_policy.title == "Updated Shipping Policy"

    def test_delete_policy(self, api_client, admin_user, shipping_policy):
        """Admin should be able to delete policies."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-detail", kwargs={"pk": shipping_policy.id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Policy.objects.filter(id=shipping_policy.id).exists()

    def test_filter_by_type_admin(self, api_client, admin_user, shipping_policy, privacy_policy):
        """Admin should be able to filter by type."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-list")
        response = api_client.get(url, {"type": PolicyType.PRIVACY_POLICY})
        
        data = response.data["data"]["results"]  # Get results from paginated response
        assert len(data) == 1
        assert data[0]["type"] == PolicyType.PRIVACY_POLICY

    def test_filter_by_active_status(self, api_client, admin_user, shipping_policy, inactive_policy):
        """Admin should be able to filter by active status."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("cms_admin:policy-admin-list")
        response = api_client.get(url, {"is_active": "false"})
        
        data = response.data["data"]["results"]  # Get results from paginated response
        assert len(data) == 1
        assert data[0]["is_active"] is False


@pytest.mark.django_db
class TestPolicyModel:
    """Test Policy model."""

    def test_type_unique_constraint(self):
        """Each policy type can only have one instance."""
        Policy.objects.create(
            type=PolicyType.SHIPPING,
            title="Shipping Policy",
            content="Content",
        )
        
        # Attempting to create another shipping policy should fail
        with pytest.raises(Exception):  # IntegrityError
            Policy.objects.create(
                type=PolicyType.SHIPPING,
                title="Another Shipping Policy",
                content="Different content",
            )

    def test_default_title_from_type(self):
        """If title is empty, it should default to type display."""
        policy = Policy.objects.create(
            type=PolicyType.PRIVACY_POLICY,
            title="",
            content="Content",
        )
        
        assert policy.title == "Privacy Policy"

    def test_str_representation(self):
        """String representation should be type display."""
        policy = Policy.objects.create(
            type=PolicyType.TERMS_CONDITIONS,
            title="Terms",
            content="Content",
        )
        
        assert str(policy) == "Terms and Conditions"

    def test_html_content_storage(self):
        """Should store HTML content from rich text editor."""
        html_content = "<h1>Title</h1><p>Paragraph with <strong>bold</strong> text.</p>"
        policy = Policy.objects.create(
            type=PolicyType.SHIPPING,
            title="Shipping",
            content=html_content,
        )
        
        policy.refresh_from_db()
        assert policy.content == html_content
