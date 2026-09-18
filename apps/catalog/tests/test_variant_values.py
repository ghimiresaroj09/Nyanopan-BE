"""Tab-2 endpoint: POST /api/v1/productvarientvalues/{product_id}/."""

import uuid

import pytest

from apps.catalog.models import ProductAttributeValue, ProductVariant
from conftest import status_data

pytestmark = pytest.mark.django_db


def _variant_entry(product, color_attr, size_attr, color, size, sku, name, price=0):
    return {
        "sku": sku,
        "name": name,
        "price": price,
        "is_active": True,
        "is_special_edition": False,
        "optionIds": [str(color.id), str(size.id)],
        "attributes": [
            {
                "attributeId": str(color_attr.id),
                "attributeValues": [str(color.id)],
            },
            {
                "attributeId": str(size_attr.id),
                "attributeValues": [str(size.id)],
            },
        ],
        "product": str(product.id),
    }


def _payload(product, color_attr, size_attr, grey, blue, size_40, size_41):
    return {
        "attributes": [
            {
                "attribute": str(color_attr.id),
                "options": [str(grey.id), str(blue.id)],
            },
            {
                "attribute": str(size_attr.id),
                "options": [str(size_40.id), str(size_41.id)],
            },
        ],
        "generatedVarients": [
            _variant_entry(
                product, color_attr, size_attr, grey, size_40,
                "TEST001", "Test Grey 40",
            ),
            _variant_entry(
                product, color_attr, size_attr, blue, size_41,
                "TEST002", "Test Blue 41",
            ),
        ],
    }


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


class TestPermissions:
    def test_unauthenticated_denied(self, api_client, product):
        response = api_client.post(f"/api/v1/productvarientvalues/{product.id}/", {})
        assert response.status_code == 401

    def test_non_staff_denied(self, plain_client, product):
        response = plain_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", {}
        )
        assert response.status_code == 403
        assert response.data["success"] is False

    def test_unknown_product_404(self, admin_client):
        response = admin_client.post(
            f"/api/v1/productvarientvalues/{uuid.uuid4()}/",
            {"attributes": [], "generatedVarients": []},
            format="json",
        )
        assert response.status_code == 404


class TestCreate:
    def test_returns_spec_shape(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        response = admin_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
        )
        assert response.status_code == 201
        assert set(response.data) == {"status", "message", "statusCode", "data"}
        assert response.data["status"] == "success"
        assert response.data["message"] == "ProductVarientValue created successfully"
        assert response.data["statusCode"] == 201

        data = response.data["data"]
        assert set(data) == {"attributes", "generatedVarients"}

        first = data["attributes"][0]
        assert set(first) == {"attribute", "options"}
        attribute = first["attribute"]
        assert set(attribute) == {
            "object", "id", "name", "isActive", "created_date", "updated_date",
        }
        assert attribute["object"] == "attribute"
        assert attribute["id"] == str(color_attr.id)
        assert attribute["name"] == "Color"
        assert attribute["isActive"] is True
        assert attribute["created_date"].endswith("Z")
        assert attribute["updated_date"].endswith("Z")
        assert [o["name"] for o in first["options"]] == ["Grey", "Blue"]
        assert first["options"][0]["object"] == "attributevalueitem"
        assert set(first["options"][0]) == {"object", "id", "name"}

        created = data["generatedVarients"]
        assert [v["sku"] for v in created] == ["TEST001", "TEST002"]
        first_variant = created[0]
        assert set(first_variant) == {
            "id", "product", "sku", "name", "price", "is_active",
            "is_special_edition", "attributeGroups", "attributes",
        }
        uuid.UUID(str(first_variant["id"]))
        assert first_variant["product"] == str(product.id)
        assert first_variant["name"] == "Test Grey 40"
        assert first_variant["price"] == 0 and not isinstance(first_variant["price"], str)
        assert first_variant["attributeGroups"] == []
        assert first_variant["attributes"] == [
            {"attributeId": str(color_attr.id), "attributeValues": [str(grey.id)]},
            {"attributeId": str(size_attr.id), "attributeValues": [str(size_40.id)]},
        ]

    def test_price_renders_as_json_number_on_the_wire(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        import json

        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        response = admin_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
        )
        assert response.status_code == 201
        response.render()
        parsed = json.loads(response.content.decode())
        prices = [v["price"] for v in parsed["data"]["generatedVarients"]]
        assert prices == [0, 0]
        assert all(isinstance(price, float) for price in prices)

    def test_creates_palette_values_and_variants(self, palette, product):
        assert ProductAttributeValue.objects.filter(product=product).count() == 4
        assert ProductVariant.objects.filter(product=product).count() == 2
        variant = ProductVariant.objects.get(sku="TEST001")
        assert variant.name == "Test Grey 40"
        assert variant.price == 0
        assert variant.options.count() == 2

    def test_bare_path_without_slash_works(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        payload["generatedVarients"] = payload["generatedVarients"][:1]
        data = status_data(
            admin_client.post(
                f"/api/v1/productvarientvalues/{product.id}", payload, format="json"
            ),
            status_code=201,
        )
        assert [v["sku"] for v in data["generatedVarients"]] == ["TEST001"]


class TestUpsert:
    def test_resave_updates_and_adds(
        self, admin_client, palette, product, color_attr, size_attr,
        grey, blue, size_40, size_41,
    ):
        first_id = palette["generatedVarients"][0]["id"]
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        # TEST001: new price/name/flags/options; TEST002 dropped from payload
        # (upsert keeps it); TEST003 brand new.
        first = payload["generatedVarients"][0]
        first.update(
            {
                "name": "Test Grey 40 v2",
                "price": "1995.50",
                "is_special_edition": True,
                "optionIds": [str(grey.id), str(size_41.id)],
                "attributes": [
                    {
                        "attributeId": str(color_attr.id),
                        "attributeValues": [str(grey.id)],
                    },
                    {
                        "attributeId": str(size_attr.id),
                        "attributeValues": [str(size_41.id)],
                    },
                ],
            }
        )
        payload["generatedVarients"] = [
            first,
            _variant_entry(
                product, color_attr, size_attr, blue, size_40,
                "TEST003", "Test Blue 40",
            ),
        ]
        data = status_data(
            admin_client.post(
                f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
            ),
            status_code=201,
        )
        assert [v["sku"] for v in data["generatedVarients"]] == ["TEST001", "TEST003"]
        updated = data["generatedVarients"][0]
        assert updated["id"] == first_id
        assert updated["name"] == "Test Grey 40 v2"
        assert updated["price"] == 1995.5
        assert updated["is_special_edition"] is True
        assert updated["attributes"][1]["attributeValues"] == [str(size_41.id)]
        assert ProductVariant.objects.filter(product=product).count() == 3
        assert ProductVariant.objects.filter(sku="TEST002").exists()

    def test_duplicate_sku_in_request_rejected(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        payload["generatedVarients"][1]["sku"] = "TEST001"
        response = admin_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
        )
        assert response.status_code == 400
        assert "generatedVarients" in response.data["errors"]
        assert ProductVariant.objects.count() == 0

    def test_sku_of_another_product_rejected(
        self, admin_client, palette, product, category, product_model,
        color_attr, size_attr, grey, blue, size_40, size_41,
    ):
        from apps.catalog.models import Product

        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        payload = _payload(other, color_attr, size_attr, grey, blue, size_40, size_41)
        payload["generatedVarients"] = payload["generatedVarients"][:1]
        response = admin_client.post(
            f"/api/v1/productvarientvalues/{other.id}/", payload, format="json"
        )
        assert response.status_code == 400
        assert "already used by another product" in str(response.data["errors"])

    def test_duplicate_combination_rejected(
        self, admin_client, product, color_attr, size_attr, grey, size_40
    ):
        payload = _payload(
            product, color_attr, size_attr, grey, grey, size_40, size_40
        )
        payload["attributes"] = payload["attributes"][:1]
        payload["generatedVarients"][1]["sku"] = "TEST999"
        payload["generatedVarients"][1]["optionIds"] = [
            str(grey.id), str(size_40.id)
        ]
        payload["generatedVarients"][1]["attributes"] = payload["generatedVarients"][0][
            "attributes"
        ]
        response = admin_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
        )
        assert response.status_code == 400
        assert ProductVariant.objects.count() == 0


class TestValidation:
    def _post(self, admin_client, product, payload):
        return admin_client.post(
            f"/api/v1/productvarientvalues/{product.id}/", payload, format="json"
        )

    def test_unknown_attribute_rejected(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        payload["attributes"][0]["attribute"] = str(uuid.uuid4())
        response = self._post(admin_client, product, payload)
        assert response.status_code == 400
        assert "attributes" in response.data["errors"]

    def test_foreign_option_rejected(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        # Size value listed under the Color palette entry.
        payload["attributes"][0]["options"] = [str(size_40.id)]
        response = self._post(admin_client, product, payload)
        assert response.status_code == 400
        assert "does not belong" in str(response.data["errors"])

    def test_option_ids_must_match_blocks(
        self, admin_client, product, color_attr, size_attr, grey, blue, size_40, size_41
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        payload["generatedVarients"][0]["optionIds"] = [str(grey.id)]
        response = self._post(admin_client, product, payload)
        assert response.status_code == 400
        assert "optionIds" in str(response.data["errors"])

    def test_product_must_match_url(
        self, admin_client, product, product_full, color_attr, size_attr,
        grey, blue, size_40, size_41,
    ):
        payload = _payload(product, color_attr, size_attr, grey, blue, size_40, size_41)
        payload["generatedVarients"][0]["product"] = str(product_full.id)
        response = self._post(admin_client, product, payload)
        assert response.status_code == 400
        assert "product" in str(response.data["errors"]).lower()
