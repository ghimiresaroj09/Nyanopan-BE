"""Service-layer tests: nested product writes, combination rules, image cleanup."""

import pytest
from django.test import TestCase

captureOnCommitCallbacks = TestCase.captureOnCommitCallbacks
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.catalog.models import (
    Category,
    Product,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantOption,
)
from apps.catalog.services.categories import CategoryService
from apps.catalog.services.images import ImageService
from apps.catalog.services.products import (
    ProductAttributeValueService,
    ProductService,
)
from apps.catalog.services.variants import VariantService
from conftest import make_pav, make_variant

pytestmark = pytest.mark.django_db


def _nested_payload(category, product_model, color_attr, size_attr, grey, blue, size_40):
    return {
        "name": "Celsi Wool Felt Slippers",
        "model": product_model,
        "gender": "UNISEX",
        "description": "Warm slippers.",
        "category": category,
        "is_featured": True,
        "key_features": [{"title": "Sole", "value": "Rubber"}],
        "attribute_values": [
            {
                "key": "grey",
                "attribute": color_attr,
                "attribute_value": grey,
                "feature_image": {
                    "name": "shop/grey-main",
                    "title": "Grey",
                    "caption": "",
                    "alt": "Grey slippers",
                },
                "additional_images": [],
            },
            {
                "key": "blue",
                "attribute": color_attr,
                "attribute_value": blue,
                "feature_image": {"name": "shop/blue-main"},
            },
            {"key": "40", "attribute": size_attr, "attribute_value": size_40},
        ],
        "variants": [
            {
                "sku": "CELSI-GREY-40",
                "price": "5995.00",
                "options": [{"key": "grey"}, {"key": "40"}],
            },
            {
                "sku": "CELSI-BLUE-40",
                "price": "6495.00",
                "is_special_edition": True,
                "options": [{"key": "blue"}, {"key": "40"}],
            },
        ],
    }


class TestProductServiceCreate:
    def test_nested_create_with_temp_keys(
        self, admin_user, category, product_model, color_attr, size_attr,
        grey, blue, size_40,
    ):
        payload = _nested_payload(
            category, product_model, color_attr, size_attr, grey, blue, size_40
        )
        product = ProductService.create_product(user=admin_user, data=payload)

        assert product.slug == "celsi-wool-felt-slippers"
        assert product.user == admin_user
        assert product.attribute_values.count() == 3
        assert product.variants.count() == 2
        grey_variant = product.variants.get(sku="CELSI-GREY-40")
        assert grey_variant.options.count() == 2
        assert grey_variant.is_special_edition is False
        blue_variant = product.variants.get(sku="CELSI-BLUE-40")
        assert blue_variant.is_special_edition is True
        grey_pav = product.attribute_values.get(attribute_value=grey)
        assert grey_pav.feature_image.name == "shop/grey-main"
        assert grey_pav.feature_image_title == "Grey"

    def test_failed_nested_create_rolls_back_everything(
        self, admin_user, category, product_model, color_attr, size_attr,
        grey, size_40,
    ):
        payload = _nested_payload(
            category, product_model, color_attr, size_attr, grey, grey, size_40
        )
        # Point the variant at a key that does not exist.
        payload["variants"][0]["options"] = [{"key": "grey"}, {"key": "missing"}]
        with pytest.raises(DRFValidationError):
            ProductService.create_product(user=admin_user, data=payload)
        assert Product.objects.count() == 0
        assert ProductAttributeValue.objects.count() == 0
        assert ProductVariant.objects.count() == 0

    def test_duplicate_combination_rejected_in_same_request(
        self, admin_user, category, product_model, color_attr, size_attr,
        grey, blue, size_40,
    ):
        payload = _nested_payload(
            category, product_model, color_attr, size_attr, grey, blue, size_40
        )
        payload["variants"].append(
            {
                "sku": "CELSI-GREY-40-B",
                "price": "5995.00",
                "options": [{"key": "grey"}, {"key": "40"}],
            }
        )
        with pytest.raises(DRFValidationError) as exc_info:
            ProductService.create_product(user=admin_user, data=payload)
        assert "variants" in exc_info.value.detail
        assert Product.objects.count() == 0


class TestProductServiceUpdate:
    def test_partial_update_keeps_variants(self, product_full):
        before = list(product_full.variants.values_list("id", flat=True))
        updated = ProductService.update_product(
            product=product_full, data={"description": "New description."}
        )
        assert updated.description == "New description."
        assert sorted(updated.variants.values_list("id", flat=True)) == sorted(before)

    def test_nested_upsert_adds_value_and_variant(
        self, product_full, color_attr, blue
    ):
        pav_41 = ProductAttributeValue.objects.get(
            product=product_full, attribute_value__name="41"
        )
        updated = ProductService.update_product(
            product=product_full,
            data={
                "variants": [
                    {
                        "sku": "CELSI-BLUE-41",
                        "price": "6495.00",
                        "options": [
                            ProductAttributeValue.objects.get(
                                product=product_full, attribute_value=blue
                            ).pk,
                            pav_41.pk,
                        ],
                    }
                ]
            },
        )
        assert updated.variants.count() == 4
        assert updated.variants.filter(sku="CELSI-BLUE-41").exists()

    def test_cross_product_option_rejected(
        self, product_full, admin_user, category, product_model, color_attr, grey
    ):
        other = Product.objects.create(
            name="Other", model=product_model, gender="MEN", category=category
        )
        foreign = make_pav(other, color_attr, grey, image_url="https://res.cloudinary.com/demo/z.jpg")
        pav_40 = ProductAttributeValue.objects.get(
            product=product_full, attribute_value__name="40"
        )
        with pytest.raises(DRFValidationError):
            ProductService.update_product(
                product=product_full,
                data={
                    "variants": [
                        {
                            "sku": "BAD-1",
                            "price": "10.00",
                            "options": [foreign.pk, pav_40.pk],
                        }
                    ]
                },
            )
        assert not product_full.variants.filter(sku="BAD-1").exists()


class TestVariantService:
    def test_duplicate_combination_rejected(self, product_full):
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        pav_40 = ProductAttributeValue.objects.get(attribute_value__name="40")
        with pytest.raises(DRFValidationError) as exc_info:
            VariantService.create_variant(
                product=product_full,
                sku="DUPLICATE-1",
                price="10.00",
                option_pav_ids=[grey_pav.pk, pav_40.pk],
            )
        assert "options" in exc_info.value.detail

    def test_two_values_of_same_attribute_rejected(self, product_full):
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        blue_pav = ProductAttributeValue.objects.get(attribute_value__name="Blue")
        with pytest.raises(DRFValidationError):
            VariantService.create_variant(
                product=product_full,
                sku="BAD-ATTR",
                price="10.00",
                option_pav_ids=[grey_pav.pk, blue_pav.pk],
            )

    def test_empty_options_rejected(self, product_full):
        with pytest.raises(DRFValidationError):
            VariantService.create_variant(
                product=product_full,
                sku="EMPTY-1",
                price="10.00",
                option_pav_ids=[],
            )

    def test_remove_option_causing_duplicate_rejected(self, product_full):
        full = ProductVariant.objects.get(sku="CELSI-GREY-40")
        option_40 = full.options.get(product_attribute_value__attribute_value__name="40")
        # A Grey-only variant already exists? No -> create the clash first:
        # remove size from CELSI-GREY-40 would make it Grey-only; create a
        # Grey-only variant, then the removal must fail.
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        make_variant(product_full, "GREY-ONLY", "1.00", [grey_pav])
        with pytest.raises(DRFValidationError):
            VariantService.remove_option(option=option_40)
        assert full.options.count() == 2

    def test_add_option(self, product, color_attr, size_attr, grey, size_40, size_41):
        grey_pav = make_pav(product, color_attr, grey, image_url="https://res.cloudinary.com/demo/x.jpg")
        pav_40 = make_pav(product, size_attr, size_40)
        pav_41 = make_pav(product, size_attr, size_41)
        variant = make_variant(product, "V-1", "10.00", [grey_pav])
        # Adding a second size... first remove nothing: add size 40 works.
        option = VariantService.add_option(variant=variant, pav_id=pav_40.pk)
        assert option.pk is not None
        # Adding another size (41) must fail: one value per attribute.
        with pytest.raises(DRFValidationError):
            VariantService.add_option(variant=variant, pav_id=pav_41.pk)


class TestImageCleanup:
    def test_replaced_product_feature_image_deleted_after_commit(self, product, monkeypatch):
        ProductService.update_product(
            product=product,
            data={"feature_image": {"name": "shop/old-product"}},
        )
        deleted = []
        monkeypatch.setattr(
            ImageService,
            "delete_image",
            staticmethod(lambda public_id: deleted.append(public_id) or True),
        )

        with captureOnCommitCallbacks(execute=True):
            ProductService.update_product(
                product=product,
                data={"feature_image": {"name": "shop/new-product"}},
            )

        assert deleted == ["shop/old-product"]

    def test_replaced_feature_image_deleted_after_commit(
        self, product, color_attr, grey, monkeypatch
    ):
        pav = make_pav(
            product, color_attr, grey,
            image_url="https://res.cloudinary.com/demo/old.jpg", public_id="shop/old",
        )
        deleted = []
        monkeypatch.setattr(
            ImageService, "delete_image", staticmethod(lambda public_id: deleted.append(public_id) or True)
        )
        with captureOnCommitCallbacks(execute=True):
            ProductAttributeValueService.update_pav(
                pav=pav,
                data={"feature_image": {"name": "shop/new"}},
            )
        assert deleted == ["shop/old"]

    def test_deleted_pav_images_cleaned_up(self, product, color_attr, grey, monkeypatch):
        pav = make_pav(
            product, color_attr, grey,
            image_url="https://res.cloudinary.com/demo/old.jpg",
            public_id="shop/old",
            additional_images=[{"url": "https://res.cloudinary.com/demo/extra.jpg", "public_id": "shop/extra"}],
        )
        deleted = []
        monkeypatch.setattr(
            ImageService, "delete_image", staticmethod(lambda public_id: deleted.append(public_id) or True)
        )
        with captureOnCommitCallbacks(execute=True):
            ProductAttributeValueService.delete_pav(pav=pav)
        assert sorted(deleted) == ["shop/extra", "shop/old"]

    def test_failed_update_does_not_delete_existing_image(
        self, product, color_attr, grey, size_40, monkeypatch
    ):
        pav = make_pav(
            product, color_attr, grey,
            image_url="https://res.cloudinary.com/demo/old.jpg", public_id="shop/old",
        )
        deleted = []
        monkeypatch.setattr(
            ImageService, "delete_image", staticmethod(lambda public_id: deleted.append(public_id) or True)
        )
        with captureOnCommitCallbacks(execute=True):
            with pytest.raises(DRFValidationError):
                # Mismatched attribute/value -> validation fails, nothing persists.
                ProductAttributeValueService.update_pav(
                    pav=pav, data={"attribute_value": size_40}
                )
        assert deleted == []
        pav.refresh_from_db()
        assert pav.feature_image.name == "shop/old"

    def test_category_image_cleanup(self, category, monkeypatch):
        deleted = []
        monkeypatch.setattr(
            ImageService, "delete_image", staticmethod(lambda public_id: deleted.append(public_id) or True)
        )
        with captureOnCommitCallbacks(execute=True):
            CategoryService.update_category(
                category=category,
                data={"image": {"name": "shop/c"}},
            )
        assert deleted == []  # nothing to replace yet
        with captureOnCommitCallbacks(execute=True):
            CategoryService.update_category(
                category=category,
                data={"image": {"name": "shop/c2"}},
            )
        assert deleted == ["shop/c"]
        with captureOnCommitCallbacks(execute=True):
            CategoryService.delete_category(category=category)
        assert deleted == ["shop/c", "shop/c2"]
        assert Category.objects.count() == 0
