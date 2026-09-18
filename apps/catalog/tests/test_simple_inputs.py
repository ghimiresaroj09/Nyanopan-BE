"""Layman-friendly inputs: human-key references, inline base64 images,
nested attribute values.

UUIDs keep working everywhere (covered by the rest of the suite); these
tests lock in the simpler alternates: slugs/names/codes/SKUs in place of
UUIDs, ``{"file": "data:image/...;base64,..."}`` for single-step JSON image
uploads, and ``{"value": [...]}`` on attribute writes.
"""

import base64
import io

import pytest
from django.test import override_settings

from apps.catalog.models import (
    Attribute,
    Category,
    Product,
    ProductAttributeValue,
)
from conftest import GREY_IMAGE, status_data, success_data

pytestmark = pytest.mark.django_db


def _png_bytes(color="red") -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _data_uri(color="red", mime="image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(_png_bytes(color)).decode()


class TestHumanKeyReferences:
    def test_product_create_with_names(
        self, admin_client, category, product_model, color_attr, size_attr,
        grey, size_40,
    ):
        data = status_data(
            admin_client.post(
                "/api/v1/admin/products/",
                {
                    "name": "Named Slippers",
                    "model": "celsi",
                    "gender": "UNISEX",
                    "category": "slippers",
                    "attribute_values": [
                        {
                            "key": "grey",
                            "attribute": "Color",
                            "attribute_value": "Grey",
                            "feature_image": {"url": GREY_IMAGE},
                        },
                        {"key": "40", "attribute": "Size", "attribute_value": "40"},
                    ],
                    "variants": [{"price": "100.00", "options": ["grey", "40"]}],
                },
                format="json",
            ),
            status_code=201,
        )
        product = Product.objects.get(slug="named-slippers")
        assert product.category_id == category.id
        assert product.model_id == product_model.id
        variant = product.variants.get()
        assert variant.sku == "NAMED-GREY-40"
        assert data["category"]["slug"] == "slippers"

    def test_forgiving_key_forms_and_mixed_uuids(
        self, admin_client, category, product_model, color_attr, grey
    ):
        data = status_data(
            admin_client.post(
                "/api/v1/admin/products/",
                {
                    "name": "Easy Slippers",
                    "model": str(product_model.id),
                    "gender": "UNISEX",
                    "category": "Slippers",
                    "attribute_values": [
                        {
                            "key": "g",
                            "attribute": "color",
                            "attribute_value": "grey",
                            "feature_image": {"url": GREY_IMAGE},
                        }
                    ],
                    "variants": [{"price": "9.99", "options": ["g"]}],
                },
                format="json",
            ),
            status_code=201,
        )
        assert data["category"]["slug"] == "slippers"
        variant = Product.objects.get(pk=data["id"]).variants.get()
        assert str(variant.price) == "9.99"

    def test_unknown_human_key_errors_guide_user(self, admin_client, product_model):
        response = admin_client.post(
            "/api/v1/admin/products/",
            {
                "name": "X",
                "model": str(product_model.id),
                "gender": "UNISEX",
                "category": "no-such-cat",
            },
            format="json",
        )
        assert response.status_code == 400
        text = str(response.data["errors"])
        assert "No category found for 'no-such-cat'" in text
        assert "UUID or the slug" in text

    def test_value_name_outside_attribute_lists_available(
        self, admin_client, product, color_attr, grey, blue
    ):
        response = admin_client.post(
            "/api/v1/admin/product-attribute-values/",
            {"product": str(product.id), "attribute": "Color", "attribute_value": "40"},
            format="json",
        )
        assert response.status_code == 400
        text = str(response.data["errors"])
        assert "No value '40' for attribute 'Color'" in text
        assert "Blue" in text and "Grey" in text

    def test_standalone_pav_accepts_names(self, admin_client, product, size_attr, size_40):
        data = success_data(
            admin_client.post(
                "/api/v1/admin/product-attribute-values/",
                {"product": product.slug, "attribute": "Size", "attribute_value": "40"},
                format="json",
            ),
            status_code=201,
        )
        assert data["attribute_name"] == "Size"
        assert data["value_name"] == "40"

    def test_standalone_variant_accepts_slug(
        self, admin_client, product_full
    ):
        blue_pav = ProductAttributeValue.objects.get(
            product=product_full, attribute_value__name="Blue"
        )
        pav_41 = ProductAttributeValue.objects.get(
            product=product_full, attribute_value__name="41"
        )
        data = success_data(
            admin_client.post(
                "/api/v1/admin/variants/",
                {
                    "product": product_full.slug,
                    "price": "10.00",
                    "options": [str(blue_pav.id), str(pav_41.id)],
                },
                format="json",
            ),
            status_code=201,
        )
        assert data["product_name"] == product_full.name

    def test_variant_option_accepts_sku(
        self, admin_client, product, color_attr, size_attr, grey, size_40
    ):
        grey_pav = ProductAttributeValue.objects.create(
            product=product, attribute=color_attr, attribute_value=grey
        )
        pav_40 = ProductAttributeValue.objects.create(
            product=product, attribute=size_attr, attribute_value=size_40
        )
        variant = success_data(
            admin_client.post(
                "/api/v1/admin/variants/",
                {
                    "product": product.slug,
                    "price": "10.00",
                    "options": [str(grey_pav.id)],
                },
                format="json",
            ),
            status_code=201,
        )
        assert variant["sku"] == "CELSI-GREY"
        data = success_data(
            admin_client.post(
                "/api/v1/admin/variant-options/",
                {"variant": "CELSI-GREY", "product_attribute_value": str(pav_40.id)},
                format="json",
            ),
            status_code=201,
        )
        assert data["variant_sku"] == "CELSI-GREY"

    def test_bulk_values_accept_attribute_name(self, admin_client, size_attr):
        data = success_data(
            admin_client.post(
                "/api/v1/admin/attribute-values/bulk/",
                {"attribute": "Size", "value": ["42"]},
                format="json",
            ),
            status_code=201,
        )
        assert [item["name"] for item in data] == ["42"]


class TestInlineBase64Images:
    def test_category_image_data_uri(self, admin_client, tmp_path):
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = success_data(
                admin_client.post(
                    "/api/v1/admin/categories/",
                    {
                        "name": "Boots",
                        "image": {"file": _data_uri(), "title": "Boots", "alt": "Boots"},
                    },
                    format="json",
                ),
                status_code=201,
            )
        assert data["image"]["url"].startswith("http://testserver/media/")
        assert data["image"]["title"] == "Boots"
        stored = Category.objects.get(slug="boots")
        assert stored.image.name and not stored.image.name.startswith("http")

    def test_nested_value_feature_image_data_uri(
        self, admin_client, tmp_path, category, product_model,
        color_attr, grey,
    ):
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = status_data(
                admin_client.post(
                    "/api/v1/admin/products/",
                    {
                        "name": "Inline Slippers",
                        "model": "celsi",
                        "gender": "UNISEX",
                        "category": "slippers",
                        "attribute_values": [
                            {
                                "key": "grey",
                                "attribute": "Color",
                                "attribute_value": "Grey",
                                "feature_image": {"file": _data_uri(color="blue")},
                            }
                        ],
                        "variants": [{"price": "5.00", "options": ["grey"]}],
                    },
                    format="json",
                ),
                status_code=201,
            )
        pav = ProductAttributeValue.objects.get(product_id=data["id"])
        assert pav.feature_image.url.startswith("/media/")

    def test_additional_images_data_uri(
        self, admin_client, tmp_path, product, size_attr, size_40
    ):
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            data = success_data(
                admin_client.post(
                    "/api/v1/admin/product-attribute-values/",
                    {
                        "product": product.slug,
                        "attribute": "Size",
                        "attribute_value": "40",
                        "additional_images": [{"file": _data_uri()}, {"file": _data_uri(color="green")}],
                    },
                    format="json",
                ),
                status_code=201,
            )
        assert len(data["additional_images"]) == 2
        for item in data["additional_images"]:
            assert item["url"].startswith("http://testserver/media/")

    def test_invalid_data_uri_rejected(self, admin_client, category):
        url = f"/api/v1/admin/categories/{category.id}/"
        for bad in (
            "data:image/png;base64,!!!",
            "data:text/plain;base64,aGVsbG8=",
            "data:image/png,not-base64",
            "no-such-part",
        ):
            response = admin_client.patch(url, {"image": {"file": bad}}, format="json")
            assert response.status_code == 400, bad


class TestNestedAttributeValues:
    def test_create_attribute_with_values(self, admin_client):
        data = success_data(
            admin_client.post(
                "/api/v1/admin/attributes/",
                {"name": "Material", "value": ["Leather", " Canvas "]},
                format="json",
            ),
            status_code=201,
        )
        assert data["values"] == ["Canvas", "Leather"]
        assert data["values_count"] == 2
        assert Attribute.objects.get(name="Material").values.count() == 2

    def test_create_without_values(self, admin_client):
        data = success_data(
            admin_client.post("/api/v1/admin/attributes/", {"name": "Pattern"}, format="json"),
            status_code=201,
        )
        assert data["values"] == []
        assert data["values_count"] == 0

    def test_create_duplicate_names_is_all_or_nothing(self, admin_client):
        response = admin_client.post(
            "/api/v1/admin/attributes/",
            {"name": "Dup", "value": ["A", "A"]},
            format="json",
        )
        assert response.status_code == 400
        assert not Attribute.objects.filter(name="Dup").exists()

    def test_update_ensures_values_idempotent(self, admin_client, size_attr, size_40):
        url = f"/api/v1/admin/attributes/{size_attr.id}/"
        data = success_data(
            admin_client.patch(url, {"value": ["40", "42"]}, format="json"),
            status_code=200,
        )
        assert data["values"] == ["40", "42"]
        data = success_data(
            admin_client.patch(url, {"value": ["40", "42"]}, format="json"),
            status_code=200,
        )
        assert data["values"] == ["40", "42"]
        assert size_attr.values.count() == 2

    def test_blank_value_rejected(self, admin_client):
        response = admin_client.post(
            "/api/v1/admin/attributes/", {"name": "X", "value": ["  "]}, format="json"
        )
        assert response.status_code == 400

    def test_values_listed_on_get(self, admin_client, color_attr, grey, blue):
        data = success_data(
            admin_client.get(f"/api/v1/admin/attributes/{color_attr.id}/"),
            status_code=200,
        )
        assert data["values"] == ["Blue", "Grey"]
        assert data["values_count"] == 2
