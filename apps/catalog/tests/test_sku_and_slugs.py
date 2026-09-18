"""SKU auto-generation + slug-follows-name behavior (service, model, API)."""

import pytest

from apps.catalog.models import Product, ProductVariant
from apps.catalog.services.variants import VariantService
from conftest import make_pav, status_data, success_data

pytestmark = pytest.mark.django_db


class TestSkuAutoGeneration:
    def test_standalone_create_generates_sku(
        self, product, color_attr, size_attr, grey, size_40
    ):
        grey_pav = make_pav(product, color_attr, grey, image_url="https://res.cloudinary.com/demo/x.jpg")
        pav_40 = make_pav(product, size_attr, size_40)
        variant = VariantService.create_variant(
            product=product,
            price="10.00",
            option_pav_ids=[pav_40.pk, grey_pav.pk],  # order-independent
        )
        assert variant.sku == "CELSI-GREY-40"

    def test_explicit_sku_respected(
        self, product, color_attr, size_attr, grey, size_40
    ):
        grey_pav = make_pav(product, color_attr, grey, image_url="https://res.cloudinary.com/demo/x.jpg")
        pav_40 = make_pav(product, size_attr, size_40)
        variant = VariantService.create_variant(
            product=product,
            price="10.00",
            option_pav_ids=[grey_pav.pk, pav_40.pk],
            sku="CUSTOM-1",
        )
        assert variant.sku == "CUSTOM-1"

    def test_collision_gets_suffix(
        self, admin_user, category, product_model, color_attr, size_attr,
        grey, size_40,
    ):
        def _make():
            product = Product.objects.create(
                user=admin_user, name="Trail Runners", model=product_model,
                gender="MEN", category=category,
            )
            grey_pav = make_pav(
                product, color_attr, grey, image_url="https://res.cloudinary.com/demo/x.jpg"
            )
            pav_40 = make_pav(product, size_attr, size_40)
            return VariantService.create_variant(
                product=product, price="1.00",
                option_pav_ids=[grey_pav.pk, pav_40.pk],
            )

        assert _make().sku == "TRAIL-GREY-40"
        assert _make().sku == "TRAIL-GREY-40-2"

    def test_nested_create_generates_sku(
        self, admin_client, category, product_model, color_attr, size_attr,
        grey, size_40,
    ):
        data = status_data(
            admin_client.post(
                "/api/v1/admin/products/",
                {
                    "name": "Celsi Wool Felt Slippers",
                    "model": str(product_model.id),
                    "gender": "UNISEX",
                    "category": str(category.id),
                    "attribute_values": [
                        {
                            "key": "grey",
                            "attribute": str(color_attr.id),
                            "attribute_value": str(grey.id),
                            "feature_image": {"url": "https://res.cloudinary.com/demo/image/upload/v1/shop/g.jpg"},
                        },
                        {"key": "40", "attribute": str(size_attr.id), "attribute_value": str(size_40.id)},
                    ],
                    "variants": [
                        {
                            "price": "5995.00",
                            "options": [{"key": "grey"}, {"key": "40"}],
                        }
                    ],
                },
                format="json",
            ),
            status_code=201,
        )
        assert (
            ProductVariant.objects.get(product_id=data["id"]).sku == "CELSI-GREY-40"
        )

    def test_options_change_does_not_rewrite_sku(self, product_full):
        from apps.catalog.models import ProductAttributeValue, ProductVariant

        variant = ProductVariant.objects.get(sku="CELSI-GREY-40")
        blue_pav = ProductAttributeValue.objects.get(attribute_value__name="Blue")
        pav_41 = ProductAttributeValue.objects.get(attribute_value__name="41")
        updated = VariantService.update_variant(
            variant=variant, option_pav_ids=[blue_pav.pk, pav_41.pk]
        )
        assert updated.sku == "CELSI-GREY-40"

    def test_orm_fallback_sku(self, product):
        from apps.catalog.models import ProductVariant

        variant = ProductVariant.objects.create(
            product=product, sku="", price="5.00"
        )
        assert variant.sku.startswith("VAR-")
        assert len(variant.sku) == 12


class TestSlugFollowsName:
    def test_product_rename_updates_slug(self, product):
        product.name = "Celsi Premium Slippers"
        product.save()
        assert product.slug == "celsi-premium-slippers"

    def test_explicit_slug_respected_on_rename(self, product):
        product.name = "Whatever"
        product.slug = "custom-slug"
        product.save()
        assert product.slug == "custom-slug"

    def test_unrelated_update_keeps_slug(self, product):
        product.description = "New description."
        product.save()
        assert product.slug == "celsi-wool-felt-slippers"

    def test_category_and_model_rename(self, category, product_model):
        category.name = "House Slippers"
        category.save()
        assert category.slug == "house-slippers"
        product_model.name = "Celsi Pro"
        product_model.save()
        assert product_model.slug == "celsi-pro"

    def test_rename_collision_gets_suffix(self, product, admin_user, category, product_model):
        Product.objects.create(
            user=admin_user, name="Premium Slippers", model=product_model,
            gender="MEN", category=category,
        )
        product.name = "Premium Slippers"
        product.save()
        assert product.slug == "premium-slippers-2"

    def test_api_product_rename(self, admin_client, product_full):
        data = status_data(
            admin_client.patch(
                f"/api/v1/admin/products/{product_full.id}/",
                {"name": "Celsi Elite Slippers"},
                format="json",
            )
        )
        assert data["name"] == "Celsi Elite Slippers"
        product_full.refresh_from_db()
        assert product_full.slug == "celsi-elite-slippers"

    def test_api_explicit_slug_kept(self, admin_client, product_full):
        data = status_data(
            admin_client.patch(
                f"/api/v1/admin/products/{product_full.id}/",
                {"name": "Whatever", "slug": "my-slug"},
                format="json",
            )
        )
        product_full.refresh_from_db()
        assert product_full.slug == "my-slug"

    def test_api_category_rename(self, admin_client, category):
        data = success_data(
            admin_client.patch(
                f"/api/v1/admin/categories/{category.id}/",
                {"name": "House Slippers"},
                format="json",
            )
        )
        assert data["slug"] == "house-slippers"

    def test_api_product_model_rename(self, admin_client, product_model):
        data = success_data(
            admin_client.patch(
                f"/api/v1/admin/product-models/{product_model.id}/",
                {"name": "Celsi Pro"},
                format="json",
            )
        )
        assert data["slug"] == "celsi-pro"
