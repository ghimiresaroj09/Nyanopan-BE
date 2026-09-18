"""Bulk attribute-value creation tests: POST /api/v1/admin/attribute-values/bulk/."""

import uuid

import pytest

from apps.catalog.models import AttributeValue
from conftest import success_data

pytestmark = pytest.mark.django_db

URL = "/api/v1/admin/attribute-values/bulk/"


class TestBulkCreate:
    def test_bulk_create(self, admin_client, size_attr):
        data = success_data(
            admin_client.post(
                URL,
                {"attribute": str(size_attr.id), "value": ["One", "Two ", "Three"]},
                format="json",
            ),
            status_code=201,
        )
        assert [item["name"] for item in data] == ["One", "Two", "Three"]
        for item in data:
            uuid.UUID(str(item["id"]))
            assert str(item["attribute"]) == str(size_attr.id)
            assert item["is_active"] is True
        assert AttributeValue.objects.filter(attribute=size_attr).count() == 3

    def test_all_or_nothing_when_name_exists(self, admin_client, size_attr, size_40):
        response = admin_client.post(
            URL,
            {"attribute": str(size_attr.id), "value": ["40", "41", "42"]},
            format="json",
        )
        assert response.status_code == 400
        assert "40" in str(response.data["errors"])
        assert AttributeValue.objects.filter(attribute=size_attr).count() == 1

    def test_duplicate_within_request_rejected(self, admin_client, size_attr):
        response = admin_client.post(
            URL,
            {"attribute": str(size_attr.id), "value": ["41", "41"]},
            format="json",
        )
        assert response.status_code == 400
        assert AttributeValue.objects.filter(attribute=size_attr).count() == 0

    def test_blank_and_empty_rejected(self, admin_client, size_attr):
        response = admin_client.post(
            URL, {"attribute": str(size_attr.id), "value": ["41", "  "]}, format="json"
        )
        assert response.status_code == 400
        response = admin_client.post(
            URL, {"attribute": str(size_attr.id), "value": []}, format="json"
        )
        assert response.status_code == 400

    def test_invalid_attribute_rejected(self, admin_client):
        response = admin_client.post(
            URL, {"attribute": str(uuid.uuid4()), "value": ["41"]}, format="json"
        )
        assert response.status_code == 400

    def test_unauthenticated_denied(self, api_client, size_attr):
        response = api_client.post(
            URL, {"attribute": str(size_attr.id), "value": ["41"]}, format="json"
        )
        assert response.status_code == 401


class TestCollectionUrlAcceptsBulkBody:
    COLLECTION_URL = "/api/v1/admin/attribute-values/"

    def test_collection_url_bulk_shape(self, admin_client, color_attr):
        data = success_data(
            admin_client.post(
                self.COLLECTION_URL,
                {"attribute": str(color_attr.id), "value": ["Red", "Black", "Blue"]},
                format="json",
            ),
            status_code=201,
        )
        assert [item["name"] for item in data] == ["Red", "Black", "Blue"]

    def test_name_and_value_together_rejected(self, admin_client, color_attr):
        response = admin_client.post(
            self.COLLECTION_URL,
            {"attribute": str(color_attr.id), "name": "Red", "value": ["Black"]},
            format="json",
        )
        assert response.status_code == 400
        assert AttributeValue.objects.filter(attribute=color_attr).count() == 0

    def test_non_list_value_rejected(self, admin_client, color_attr):
        response = admin_client.post(
            self.COLLECTION_URL,
            {"attribute": str(color_attr.id), "value": "Red"},
            format="json",
        )
        assert response.status_code == 400

    def test_single_shape_still_works(self, admin_client, color_attr):
        data = success_data(
            admin_client.post(
                self.COLLECTION_URL,
                {"attribute": str(color_attr.id), "name": "Red"},
                format="json",
            ),
            status_code=201,
        )
        assert data["name"] == "Red"
