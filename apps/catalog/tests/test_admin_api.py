"""Admin API tests: permissions, CRUD, nested writes, validation envelopes."""

import uuid

import pytest
from PIL import Image

from apps.catalog.models import (
    Category,
    Product,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantOption,
)
from conftest import BLUE_IMAGE, GREY_IMAGE, status_data, success_data

pytestmark = pytest.mark.django_db


class TestPermissions:
    def test_unauthenticated_admin_access_denied(self, api_client, product):
        assert api_client.get("/api/v1/admin/products/").status_code == 401
        assert api_client.post("/api/v1/admin/products/", {}).status_code == 401

    def test_non_staff_access_denied(self, plain_client, product):
        response = plain_client.get("/api/v1/admin/products/")
        assert response.status_code == 403
        assert response.data["success"] is False

    def test_staff_access_allowed(self, admin_client):
        status_data(admin_client.get("/api/v1/admin/products/"))


class TestUuidIds:
    def test_ids_are_valid_uuids(self, admin_client, product_full):
        data = status_data(admin_client.get(f"/api/v1/admin/products/{product_full.id}/"))
        uuid.UUID(str(data["id"]))
        uuid.UUID(str(data["model"]["id"]))
        uuid.UUID(str(data["category"]["id"]))
        for pav_id in product_full.attribute_values.values_list("id", flat=True):
            uuid.UUID(str(pav_id))
        for variant_id in product_full.variants.values_list("id", flat=True):
            uuid.UUID(str(variant_id))

    def test_malformed_uuid_returns_404(self, admin_client):
        response = admin_client.get("/api/v1/admin/products/not-a-uuid/")
        assert response.status_code == 404
        assert response.data["success"] is False

    def test_unknown_uuid_returns_404(self, admin_client):
        response = admin_client.get(f"/api/v1/admin/products/{uuid.uuid4()}/")
        assert response.status_code == 404
        assert response.data["success"] is False


class TestCategoryAdmin:
    def test_create_category_with_image_object(self, admin_client):
        data = success_data(
            admin_client.post(
                "/api/v1/admin/categories/",
                {
                    "name": "Boots",
                    "description": "Sturdy boots.",
                    "image": {
                        "url": "https://res.cloudinary.com/demo/image/upload/v1/shop/boots.jpg",
                        "public_id": "shop/boots",
                        "title": "Boots",
                        "caption": "",
                        "alt": "Boots",
                    },
                },
                format="json",
            ),
            status_code=201,
        )
        assert data["slug"] == "boots"
        assert data["image"]["public_id"] == "shop/boots"
        assert data["image"]["url"] == "http://testserver/media/shop/boots"

    def test_duplicate_category_rejected(self, admin_client, category):
        response = admin_client.post(
            "/api/v1/admin/categories/", {"name": "Slippers"}, format="json"
        )
        assert response.status_code == 400
        assert response.data["success"] is False
        assert "name" in response.data["errors"]

    def test_delete_category_with_products_rejected(self, admin_client, product_full):
        response = admin_client.delete(f"/api/v1/admin/categories/{product_full.category_id}/")
        assert response.status_code == 400
        assert response.data["success"] is False

    def test_delete_unused_category(self, admin_client, category):
        response = admin_client.delete(f"/api/v1/admin/categories/{category.id}/")
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["message"] == "Deleted successfully."
        assert Category.objects.count() == 0

    def test_clear_category_image(self, admin_client, category):
        category.image = "shop/old"
        category.save()
        data = success_data(
            admin_client.patch(
                f"/api/v1/admin/categories/{category.id}/", {"image": None}, format="json"
            )
        )
        assert data["image"] is None


class TestNestedProductAdmin:
    def _payload(self, category, product_model, color_attr, size_attr, grey, size_40):
        return {
            "name": "Celsi Wool Felt Slippers",
            "model": str(product_model.id),
            "gender": "UNISEX",
            "description": "Warm slippers.",
            "category": str(category.id),
            "is_featured": True,
            "key_features": [{"title": "Sole", "value": "Rubber"}],
            "attribute_values": [
                {
                    "key": "grey",
                    "attribute": str(color_attr.id),
                    "attribute_value": str(grey.id),
                    "feature_image": {"url": GREY_IMAGE, "public_id": "shop/grey-main"},
                },
                {"key": "40", "attribute": str(size_attr.id), "attribute_value": str(size_40.id)},
            ],
            "variants": [
                {
                    "sku": "CELSI-GREY-40",
                    "price": "5995.00",
                    "options": [{"key": "grey"}, {"key": "40"}],
                }
            ],
        }

    def test_nested_product_create(
        self, admin_client, category, product_model, color_attr, size_attr,
        grey, size_40,
    ):
        payload = self._payload(
            category, product_model, color_attr, size_attr, grey, size_40
        )
        data = status_data(
            admin_client.post("/api/v1/admin/products/", payload, format="json"),
            status_code=201,
        )
        # Lean response shape: scalars plus nested model/category objects.
        assert data["name"] == "Celsi Wool Felt Slippers"
        assert data["model"] == {
            "id": str(product_model.id),
            "name": "Celsi",
            "slug": "celsi",
            "description": "",
            "isActive": True,
        }
        assert data["category"]["slug"] == "slippers"
        assert data["category"]["isActive"] is True
        assert data["key_features"] == [{"title": "Sole", "value": "Rubber"}]
        assert "attribute_values" not in data and "variants" not in data
        # ...but the nested rows were still created underneath.
        product = Product.objects.get(pk=data["id"])
        assert product.slug == "celsi-wool-felt-slippers"
        assert product.attribute_values.count() == 2
        variant = product.variants.get()
        assert variant.sku == "CELSI-GREY-40"
        assert sorted(
            o.product_attribute_value.attribute.name for o in variant.options.all()
        ) == ["Color", "Size"]

    def test_nested_create_failure_leaves_nothing(
        self, admin_client, category, product_model, color_attr, size_attr,
        grey, size_40,
    ):
        payload = self._payload(
            category, product_model, color_attr, size_attr, grey, size_40
        )
        payload["variants"][0]["options"] = [{"key": "grey"}, {"key": "nope"}]
        response = admin_client.post("/api/v1/admin/products/", payload, format="json")
        assert response.status_code == 400
        assert Product.objects.count() == 0

    def test_partial_update_does_not_touch_variants(self, admin_client, product_full):
        variant_ids = sorted(str(v) for v in product_full.variants.values_list("id", flat=True))
        data = status_data(
            admin_client.patch(
                f"/api/v1/admin/products/{product_full.id}/",
                {"description": "Updated."},
                format="json",
            )
        )
        assert data["description"] == "Updated."
        assert sorted(str(v) for v in product_full.variants.values_list("id", flat=True)) == variant_ids

    def test_add_variant_through_product_update(
        self, admin_client, product_full
    ):
        blue_pav = ProductAttributeValue.objects.get(attribute_value__name="Blue")
        pav_41 = ProductAttributeValue.objects.get(attribute_value__name="41")
        data = status_data(
            admin_client.patch(
                f"/api/v1/admin/products/{product_full.id}/",
                {
                    "variants": [
                        {
                            "sku": "CELSI-BLUE-41",
                            "price": "6495.00",
                            "is_special_edition": True,
                            "options": [str(blue_pav.id), str(pav_41.id)],
                        }
                    ]
                },
                format="json",
            )
        )
        assert data["name"] == product_full.name
        assert product_full.variants.count() == 4
        assert product_full.variants.filter(sku="CELSI-BLUE-41").exists()

    def test_duplicate_combination_rejected(self, admin_client, product_full):
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        pav_40 = ProductAttributeValue.objects.get(attribute_value__name="40")
        response = admin_client.patch(
            f"/api/v1/admin/products/{product_full.id}/",
            {
                "variants": [
                    {
                        "sku": "DUP-1",
                        "price": "10.00",
                        "options": [str(grey_pav.id), str(pav_40.id)],
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 400
        assert response.data["success"] is False

    def test_invalid_key_features_rejected(self, admin_client, product_full):
        response = admin_client.patch(
            f"/api/v1/admin/products/{product_full.id}/",
            {"key_features": [{"title": "Only title"}]},
            format="json",
        )
        assert response.status_code == 400
        assert "key_features" in response.data["errors"]

    def test_invalid_gender_rejected(self, admin_client, product_full):
        response = admin_client.patch(
            f"/api/v1/admin/products/{product_full.id}/",
            {"gender": "ALIEN"},
            format="json",
        )
        assert response.status_code == 400

    def test_delete_product_with_full_config(self, admin_client, product_full):
        response = admin_client.delete(f"/api/v1/admin/products/{product_full.id}/")
        assert response.status_code == 200
        assert response.data == {
            "status": "success",
            "message": "Product deleted successfully.",
            "statusCode": 200,
            "data": {},
        }
        assert Product.objects.count() == 0
        assert ProductAttributeValue.objects.count() == 0
        assert ProductVariant.objects.count() == 0
        assert ProductVariantOption.objects.count() == 0


class TestAttributeAdmin:
    def test_attribute_crud(self, admin_client):
        created = success_data(
            admin_client.post(
                "/api/v1/admin/attributes/",
                {"name": "Material", "requires_image": False},
                format="json",
            ),
            status_code=201,
        )
        attribute_id = created["id"]
        success_data(
            admin_client.post(
                "/api/v1/admin/attribute-values/",
                {"attribute": attribute_id, "name": "Leather"},
                format="json",
            ),
            status_code=201,
        )
        duplicate = admin_client.post(
            "/api/v1/admin/attribute-values/",
            {"attribute": attribute_id, "name": "Leather"},
            format="json",
        )
        assert duplicate.status_code == 400


class TestProductAttributeValueAdmin:
    def test_color_requires_image(self, admin_client, product, color_attr, grey):
        response = admin_client.post(
            "/api/v1/admin/product-attribute-values/",
            {"product": str(product.id), "attribute": str(color_attr.id), "attribute_value": str(grey.id)},
            format="json",
        )
        assert response.status_code == 400
        assert "feature_image" in response.data["errors"]

    def test_create_and_update_pav(
        self, admin_client, product, color_attr, size_attr, grey, size_40
    ):
        created = success_data(
            admin_client.post(
                "/api/v1/admin/product-attribute-values/",
                {
                    "product": str(product.id),
                    "attribute": str(color_attr.id),
                    "attribute_value": str(grey.id),
                    "feature_image": {"url": GREY_IMAGE},
                    "additional_images": [{"url": BLUE_IMAGE, "title": "Alt"}],
                },
                format="json",
            ),
            status_code=201,
        )
        assert created["additional_images"][0]["title"] == "Alt"
        pav_id = created["id"]
        # Mismatched value update must fail.
        bad = admin_client.patch(
            f"/api/v1/admin/product-attribute-values/{pav_id}/",
            {"attribute_value": str(size_40.id)},
            format="json",
        )
        assert bad.status_code == 400

    def test_delete_pav_used_by_variant_rejected(self, admin_client, product_full):
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        response = admin_client.delete(f"/api/v1/admin/product-attribute-values/{grey_pav.id}/")
        assert response.status_code == 400


class TestVariantAdmin:
    def test_variant_crud(self, admin_client, product, color_attr, size_attr, grey, size_40):
        grey_pav = ProductAttributeValue.objects.create(
            product=product, attribute=color_attr, attribute_value=grey,
            feature_image=GREY_IMAGE,
        )
        pav_40 = ProductAttributeValue.objects.create(
            product=product, attribute=size_attr, attribute_value=size_40
        )
        created = success_data(
            admin_client.post(
                "/api/v1/admin/variants/",
                {
                    "product": str(product.id),
                    "sku": "V-1",
                    "price": "100.00",
                    "is_special_edition": True,
                    "options": [str(grey_pav.id), str(pav_40.id)],
                },
                format="json",
            ),
            status_code=201,
        )
        assert created["is_special_edition"] is True
        variant_id = created["id"]
        # Duplicate SKU rejected.
        duplicate = admin_client.post(
            "/api/v1/admin/variants/",
            {
                "product": str(product.id),
                "sku": "V-1",
                "price": "100.00",
                "options": [str(grey_pav.id), str(pav_40.id)],
            },
            format="json",
        )
        assert duplicate.status_code == 400
        # Partial update keeps options when omitted.
        patched = success_data(
            admin_client.patch(
                f"/api/v1/admin/variants/{variant_id}/",
                {"price": "120.00"},
                format="json",
            )
        )
        assert len(patched["options_detail"]) == 2

    def test_cross_product_option_rejected(
        self, admin_client, product_full, admin_user, category, product_model,
        color_attr, grey,
    ):
        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        foreign = ProductAttributeValue.objects.create(
            product=other, attribute=color_attr, attribute_value=grey,
            feature_image=GREY_IMAGE,
        )
        pav_40 = ProductAttributeValue.objects.get(attribute_value__name="40")
        response = admin_client.post(
            "/api/v1/admin/variants/",
            {
                "product": str(product_full.id),
                "sku": "CROSS-1",
                "price": "10.00",
                "options": [str(foreign.id), str(pav_40.id)],
            },
            format="json",
        )
        assert response.status_code == 400
        assert "options" in response.data["errors"]

    def test_variant_option_endpoints(self, admin_client, product_full):
        variant = ProductVariant.objects.get(sku="CELSI-GREY-40")
        pav_41 = ProductAttributeValue.objects.get(attribute_value__name="41")
        # Add a second size -> must fail (one value per attribute).
        bad = admin_client.post(
            "/api/v1/admin/variant-options/",
            {"variant": str(variant.id), "product_attribute_value": str(pav_41.id)},
            format="json",
        )
        assert bad.status_code == 400
        # Removing size 40 from Grey+40 would duplicate nothing here (no Grey-only
        # variant exists), so first create the clash, then removal must fail.
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        ProductVariant.objects.create(
            product=product_full, sku="GREY-ONLY", price="1.00"
        )
        from apps.catalog.models import ProductVariantOption

        ProductVariantOption.objects.create(
            variant=ProductVariant.objects.get(sku="GREY-ONLY"),
            product_attribute_value=grey_pav,
        )
        option_40 = variant.options.get(product_attribute_value__attribute_value__name="40")
        response = admin_client.delete(f"/api/v1/admin/variant-options/{option_40.id}/")
        assert response.status_code == 400


class TestProductModelAdmin:
    def test_product_model_crud(self, admin_client):
        created = success_data(
            admin_client.post(
                "/api/v1/admin/product-models/", {"name": "Kumari"}, format="json"
            ),
            status_code=201,
        )
        assert created["slug"] == "kumari"
