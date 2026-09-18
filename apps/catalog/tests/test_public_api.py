"""Public API tests: listing, detail, search, filters, sorting, pagination."""

import uuid

import pytest

from apps.catalog.models import Product
from conftest import make_pav, make_variant, success_data

pytestmark = pytest.mark.django_db


def _assert_uuid(value):
    uuid.UUID(str(value))  # raises unless a valid UUID


class TestCategories:
    def test_list_categories(self, api_client, category):
        data = success_data(api_client.get("/api/v1/categories/"))
        assert data["count"] == 1
        item = data["results"][0]
        assert item["slug"] == "slippers"
        assert "product_count" in item
        _assert_uuid(item["id"])

    def test_inactive_category_excluded(self, api_client, inactive_category):
        data = success_data(api_client.get("/api/v1/categories/"))
        assert data["count"] == 0
        response = api_client.get(f"/api/v1/categories/{inactive_category.slug}/")
        assert response.status_code == 404

    def test_retrieve_category(self, api_client, category):
        data = success_data(api_client.get("/api/v1/categories/slippers/"))
        assert data["name"] == "Slippers"


class TestProductModelsAndAttributes:
    def test_list_product_models(self, api_client, product_model):
        data = success_data(api_client.get("/api/v1/product-models/"))
        assert data["results"][0]["slug"] == "celsi"

    def test_list_attributes_with_values(self, api_client, color_attr, grey, blue, size_attr):
        data = success_data(api_client.get("/api/v1/attributes/"))
        color = next(item for item in data["results"] if item["name"] == "Color")
        assert color["requires_image"] is True
        assert {v["name"] for v in color["values"]} == {"Grey", "Blue"}

    def test_retrieve_attribute(self, api_client, size_attr, size_40):
        data = success_data(api_client.get(f"/api/v1/attributes/{size_attr.id}/"))
        assert data["values"][0]["name"] == "40"


class TestProductList:
    def test_list_products(self, api_client, product_full):
        data = success_data(api_client.get("/api/v1/products/"))
        assert set(data) == {"count", "next", "previous", "results"}
        assert data["count"] == 1
        item = data["results"][0]
        assert item["slug"] == product_full.slug
        assert item["category"]["slug"] == "slippers"
        assert item["model"]["name"] == "Celsi"
        assert item["is_featured"] is True
        assert item["price_range"]["min_price"] == "5995.00"
        assert item["price_range"]["max_price"] == "6495.00"
        assert set(item["price_range"]) == {"min_price", "max_price"}
        assert item["primary_image"]["url"] == "http://testserver/media/shop/grey-main"
        _assert_uuid(item["id"])
        _assert_uuid(item["category"]["id"])
        _assert_uuid(item["model"]["id"])

    def test_inactive_product_excluded(self, api_client, product_full):
        product_full.is_active = False
        product_full.save()
        data = success_data(api_client.get("/api/v1/products/"))
        assert data["count"] == 0

    def test_product_in_inactive_category_excluded(self, api_client, product_full, category):
        category.is_active = False
        category.save()
        data = success_data(api_client.get("/api/v1/products/"))
        assert data["count"] == 0

    def test_filter_by_category(self, api_client, product_full):
        data = success_data(api_client.get("/api/v1/products/?category=slippers"))
        assert data["count"] == 1
        data = success_data(api_client.get("/api/v1/products/?category=boots"))
        assert data["count"] == 0

    def test_filter_by_gender(self, api_client, product_full):
        assert success_data(api_client.get("/api/v1/products/?gender=UNISEX"))["count"] == 1
        assert success_data(api_client.get("/api/v1/products/?gender=MEN"))["count"] == 0

    def test_filter_by_featured(self, api_client, product_full):
        assert success_data(api_client.get("/api/v1/products/?is_featured=true"))["count"] == 1
        assert success_data(api_client.get("/api/v1/products/?is_featured=false"))["count"] == 0

    def test_filter_by_price(self, api_client, product_full):
        assert success_data(api_client.get("/api/v1/products/?min_price=6000"))["count"] == 1
        assert success_data(api_client.get("/api/v1/products/?min_price=7000"))["count"] == 0
        assert success_data(api_client.get("/api/v1/products/?max_price=6000"))["count"] == 1
        assert success_data(api_client.get("/api/v1/products/?max_price=1000"))["count"] == 0

    def test_search(self, api_client, product_full):
        assert success_data(api_client.get("/api/v1/products/?search=slipper"))["count"] == 1
        assert success_data(api_client.get("/api/v1/products/?search=celsi"))["count"] == 1
        assert success_data(api_client.get("/api/v1/products/?search=sneaker"))["count"] == 0

    def test_ordering_by_price(
        self, api_client, product_full, admin_user, category, product_model,
        color_attr, grey,
    ):
        cheap = Product.objects.create(
            name="Budget Slippers", model=product_model, gender="MEN", category=category
        )
        pav = make_pav(cheap, color_attr, grey, image_url="https://res.cloudinary.com/demo/c.jpg")
        make_variant(cheap, "CHEAP-1", "999.00", [pav])
        ascending = success_data(api_client.get("/api/v1/products/?ordering=price"))["results"]
        assert [item["slug"] for item in ascending] == [cheap.slug, product_full.slug]
        descending = success_data(api_client.get("/api/v1/products/?ordering=-price"))["results"]
        assert [item["slug"] for item in descending] == [product_full.slug, cheap.slug]

    def test_ordering_by_name_and_created_at(self, api_client, product_full):
        success_data(api_client.get("/api/v1/products/?ordering=name"))
        success_data(api_client.get("/api/v1/products/?ordering=-created_at"))

    def test_pagination(self, api_client, product_full):
        data = success_data(api_client.get("/api/v1/products/?page_size=1"))
        assert data["count"] == 1
        assert len(data["results"]) == 1


class TestProductDetail:
    def test_detail_structure(self, api_client, product_full):
        data = success_data(api_client.get(f"/api/v1/products/{product_full.slug}/"))
        assert data["name"] == "Celsi Wool Felt Slippers"
        assert data["gender"] == "UNISEX"
        assert data["category"] == {"id": data["category"]["id"], "name": "Slippers", "slug": "slippers"}
        assert data["model"]["name"] == "Celsi"
        assert data["key_features"][0] == {"title": "Upper Material", "value": "Wool Felt"}

        color = next(group for group in data["attributes"] if group["attribute"] == "Color")
        assert {v["name"] for v in color["values"]} == {"Grey", "Blue"}
        grey_value = next(v for v in color["values"] if v["name"] == "Grey")
        assert grey_value["feature_image"]["url"] == "http://testserver/media/shop/grey-main"
        assert len(grey_value["additional_images"]) == 1
        assert grey_value["additional_images"][0]["url"] == "http://testserver/media/shop/grey-side"

        size = next(group for group in data["attributes"] if group["attribute"] == "Size")
        assert {v["name"] for v in size["values"]} == {"40", "41"}
        assert size["values"][0]["feature_image"] is None

        assert len(data["variants"]) == 3
        special = next(v for v in data["variants"] if v["sku"] == "CELSI-BLUE-40")
        assert special["price"] == "6495.00"
        assert special["is_special_edition"] is True
        assert {(o["attribute"], o["value"]) for o in special["options"]} == {
            ("Color", "Blue"), ("Size", "40")
        }
        _assert_uuid(data["id"])
        _assert_uuid(special["id"])
        for option in special["options"]:
            _assert_uuid(option["product_attribute_value"])

    def test_frontend_variant_matching(self, api_client, product_full):
        """The frontend matches selected option ids against variant options."""
        data = success_data(api_client.get(f"/api/v1/products/{product_full.slug}/"))
        by_name = {}
        for group in data["attributes"]:
            for value in group["values"]:
                by_name[(group["attribute"], value["name"])] = value["id"]
        selected = {by_name[("Color", "Grey")], by_name[("Size", "40")]}
        matched = [
            v for v in data["variants"]
            if {o["product_attribute_value"] for o in v["options"]} == selected
        ]
        assert len(matched) == 1
        assert matched[0]["sku"] == "CELSI-GREY-40"

    def test_inactive_product_returns_404(self, api_client, product_full):
        product_full.is_active = False
        product_full.save()
        response = api_client.get(f"/api/v1/products/{product_full.slug}/")
        assert response.status_code == 404
        assert response.data["success"] is False

    def test_inactive_variant_and_value_hidden(self, api_client, product_full):
        variant = product_full.variants.get(sku="CELSI-GREY-41")
        variant.is_active = False
        variant.save()
        data = success_data(api_client.get(f"/api/v1/products/{product_full.slug}/"))
        assert {v["sku"] for v in data["variants"]} == {"CELSI-GREY-40", "CELSI-BLUE-40"}


class TestDocs:
    def test_schema_and_docs_available(self, api_client):
        assert api_client.get("/api/schema/").status_code == 200
        assert api_client.get("/api/docs/").status_code == 200
