"""Tab-2 endpoint: PATCH /api/v1/productvarientvalues/{product_id}/ (bulk update)."""

import uuid

import pytest

from apps.catalog.models import Product, ProductVariant
from apps.catalog.tests.test_variant_values import _payload
from conftest import status_data

pytestmark = pytest.mark.django_db


@pytest.fixture
def palette(admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41):
    payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
    data = status_data(
        admin_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
        ),
        status_code=201,
    )
    return data


def _patch(client, product_id, payload):
    return client.patch(
        f"/api/v1/productvarientvalues/{product_id}/", payload, format="json"
    )


class TestPermissions:
    def test_unauthenticated_denied(self, api_client, product):
        response = api_client.patch(
            f"/api/v1/productvarientvalues/{product.id}/", {}
        )
        assert response.status_code == 401

    def test_non_staff_denied(self, plain_client, product):
        response = plain_client.patch(
            f"/api/v1/productvarientvalues/{product.id}/", {}
        )
        assert response.status_code == 403
        assert response.data["success"] is False

    def test_unknown_product_404(self, admin_client):
        response = admin_client.patch(
            f"/api/v1/productvarientvalues/{uuid.uuid4()}/",
            {"generatedVarients": [{"sku": "NOPE", "price": "10.00"}]},
            format="json",
        )
        assert response.status_code == 404


class TestBulkUpdate:
    def test_returns_envelope_and_updated_variants(
        self, admin_client, palette, product
    ):
        payload = {
            "generatedVarients": [
                # Reversed order: the echo follows request order.
                {"sku": "TEST002", "price": "1995.50", "is_special_edition": True},
                {"sku": "TEST001", "name": "Test Grey 40 v2", "is_active": False},
            ]
        }
        response = _patch(admin_client, product.id, payload)
        assert response.status_code == 200
        assert set(response.data) == {"status", "message", "statusCode", "data"}
        assert response.data["message"] == "ProductVarientValues updated successfully"
        assert response.data["statusCode"] == 200

        data = response.data["data"]
        assert set(data) == {"attributes", "generatedVarients"}
        assert [v["sku"] for v in data["generatedVarients"]] == [
            "TEST002",
            "TEST001",
        ]
        second, first = data["generatedVarients"]
        assert second["price"] == 1995.5
        assert second["is_special_edition"] is True
        assert second["name"] == "Test Blue 41"
        assert first["name"] == "Test Grey 40 v2"
        assert first["is_active"] is False
        assert first["price"] == 0
        assert set(first) == {
            "id", "product", "sku", "name", "price", "is_active",
            "is_special_edition", "attributeGroups", "attributes",
        }

        groups = data["attributes"]
        assert [g["attribute"]["name"] for g in groups] == ["Color", "Size"]
        assert set(groups[0]) == {"attribute", "options"}
        assert [o["name"] for o in groups[0]["options"]] == ["Blue", "Grey"]
        assert [o["name"] for o in groups[1]["options"]] == ["40", "41"]

    def test_only_sent_fields_change(self, admin_client, palette, product):
        before = ProductVariant.objects.get(sku="TEST001")
        before_options = sorted(
            before.options.values_list("product_attribute_value_id", flat=True)
        )
        data = status_data(
            _patch(
                admin_client,
                product.id,
                {"generatedVarients": [{"sku": "TEST001", "price": "6495.00"}]},
            ),
            status_code=200,
        )
        assert data["generatedVarients"][0]["price"] == 6495.0
        after = ProductVariant.objects.get(sku="TEST001")
        assert after.price == 6495
        assert after.name == before.name
        assert after.is_active == before.is_active
        assert after.is_special_edition == before.is_special_edition
        assert (
            sorted(
                after.options.values_list(
                    "product_attribute_value_id", flat=True
                )
            )
            == before_options
        )
        untouched = ProductVariant.objects.get(sku="TEST002")
        assert untouched.price == 0
        assert untouched.name == "Test Blue 41"

    def test_bare_path_without_slash_works(self, admin_client, palette, product):
        data = status_data(
            admin_client.patch(
                f"/api/v1/productvarientvalues/{product.id}",
                {"generatedVarients": [{"sku": "TEST001", "price": "1.00"}]},
                format="json",
            ),
            status_code=200,
        )
        assert [v["sku"] for v in data["generatedVarients"]] == ["TEST001"]
        assert ProductVariant.objects.get(sku="TEST001").price == 1


class TestAtomicFailure:
    def test_unknown_sku_fails_everything(self, admin_client, palette, product):
        payload = {
            "generatedVarients": [
                {"sku": "TEST001", "price": "111.00"},
                {"sku": "NOPE", "price": "222.00"},
            ]
        }
        response = _patch(admin_client, product.id, payload)
        assert response.status_code == 400
        assert "generatedVarients" in response.data["errors"]
        assert "Unknown SKU: NOPE." in str(response.data["errors"])
        assert ProductVariant.objects.get(sku="TEST001").price == 0
        assert ProductVariant.objects.filter(product=product).count() == 2

    def test_sku_of_another_product_rejected(
        self, admin_client, palette, category, product_model
    ):
        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        response = _patch(
            admin_client,
            other.id,
            {"generatedVarients": [{"sku": "TEST001", "price": "5.00"}]},
        )
        assert response.status_code == 400
        assert "already used by another product" in str(response.data["errors"])
        assert ProductVariant.objects.get(sku="TEST001").price == 0


class TestValidation:
    def test_duplicate_sku_in_request_rejected(
        self, admin_client, palette, product
    ):
        payload = {
            "generatedVarients": [
                {"sku": "TEST001", "price": "1.00"},
                {"sku": "TEST001", "price": "2.00"},
            ]
        }
        response = _patch(admin_client, product.id, payload)
        assert response.status_code == 400
        assert "Duplicate SKU" in str(response.data["errors"])
        assert ProductVariant.objects.get(sku="TEST001").price == 0

    def test_row_without_changes_rejected(self, admin_client, palette, product):
        response = _patch(
            admin_client, product.id, {"generatedVarients": [{"sku": "TEST001"}]}
        )
        assert response.status_code == 400
        assert "at least one field" in str(response.data["errors"])

    def test_blank_sku_rejected(self, admin_client, palette, product):
        response = _patch(
            admin_client,
            product.id,
            {"generatedVarients": [{"sku": "  ", "price": "1.00"}]},
        )
        assert response.status_code == 400
        assert "blank" in str(response.data["errors"]).lower()

    def test_negative_price_rejected(self, admin_client, palette, product):
        response = _patch(
            admin_client,
            product.id,
            {"generatedVarients": [{"sku": "TEST001", "price": "-5.00"}]},
        )
        assert response.status_code == 400
        assert ProductVariant.objects.get(sku="TEST001").price == 0

    def test_empty_list_rejected(self, admin_client, palette, product):
        response = _patch(admin_client, product.id, {"generatedVarients": []})
        assert response.status_code == 400

    def test_missing_key_rejected(self, admin_client, palette, product):
        response = _patch(admin_client, product.id, {})
        assert response.status_code == 400
        assert "generatedVarients" in response.data["errors"]
