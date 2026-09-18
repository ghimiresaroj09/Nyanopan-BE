"""Model tests: slugs, constraints, relationships, model-level validation."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.catalog.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttributeImage,
    ProductAttributeValue,
    ProductModel,
    ProductVariant,
    ProductVariantOption,
)
from conftest import make_pav, make_variant

pytestmark = pytest.mark.django_db


def _build_product(**overrides):
    defaults = {
        "name": "Test Product",
        "model": ProductModel.objects.create(name="M1"),
        "gender": "MEN",
        "category": Category.objects.create(name="C1"),
    }
    defaults.update(overrides)
    return Product(**defaults)


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class TestCategory:
    def test_create_category(self, category):
        assert category.pk is not None
        assert category.slug == "slippers"
        assert category.is_active is True

    def test_slug_generated_when_missing(self, db):
        category = Category.objects.create(name="Running Shoes")
        assert category.slug == "running-shoes"

    def test_slug_uniqueness(self, db):
        Category.objects.create(name="Red Shoes")
        other = Category.objects.create(name="Red Shoes!")
        assert other.slug == "red-shoes-2"

    def test_duplicate_name_rejected(self, category):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Slippers")

    def test_explicit_duplicate_slug_rejected(self, category):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Other", slug="slippers")

    def test_delete_protected_when_referenced(self, product, category):
        with pytest.raises(ProtectedError):
            category.delete()

    def test_delete_allowed_when_unreferenced(self, category):
        category.delete()
        assert Category.objects.count() == 0


# ---------------------------------------------------------------------------
# ProductModel
# ---------------------------------------------------------------------------
class TestProductModelModel:
    def test_slug_generated(self, db):
        model = ProductModel.objects.create(name="Celsi Wool Felt Slippers")
        assert model.slug == "celsi-wool-felt-slippers"

    def test_duplicate_name_rejected(self, product_model):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductModel.objects.create(name="Celsi")

    def test_delete_protected_when_referenced(self, product, product_model):
        with pytest.raises(ProtectedError):
            product_model.delete()


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class TestProduct:
    def test_create_product(self, product):
        assert product.slug == "celsi-wool-felt-slippers"
        assert product.key_features[0] == {"title": "Upper Material", "value": "Wool Felt"}

    def test_slug_uniqueness(self, product):
        other = _build_product(name="Celsi Wool Felt Slippers!")
        other.save()
        assert other.slug == "celsi-wool-felt-slippers-2"

    def test_invalid_gender_rejected(self):
        product = _build_product(gender="INVALID")
        with pytest.raises(ValidationError) as exc_info:
            product.full_clean()
        assert "gender" in exc_info.value.message_dict

    @pytest.mark.parametrize(
        "key_features",
        [
            "not-a-list",
            {"title": "x", "value": "y"},
            [123],
            ["Upper"],
            [{"title": "Upper"}],  # missing value
            [{"value": "Leather"}],  # missing title
            [{"title": "", "value": "Leather"}],  # empty title
            [{"title": "Upper", "value": "  "}],  # empty value
        ],
    )
    def test_invalid_key_features_rejected(self, key_features):
        product = _build_product(key_features=key_features)
        with pytest.raises(ValidationError):
            product.full_clean()

    def test_empty_key_features_allowed(self):
        product = _build_product(key_features=[])
        product.full_clean()  # must not raise

    def test_category_and_model_relationships(self, product, category, product_model):
        assert product.category == category
        assert product.model == product_model

    def test_duplicate_slug_rejected(self, product):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                _build_product(name="Other", slug=product.slug).save()


# ---------------------------------------------------------------------------
# Attribute / AttributeValue
# ---------------------------------------------------------------------------
class TestAttributes:
    def test_create_attribute(self, color_attr):
        assert color_attr.requires_image is True

    def test_duplicate_attribute_rejected(self, color_attr):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Attribute.objects.create(name="Color")

    def test_create_attribute_value(self, grey, color_attr):
        assert grey.attribute == color_attr

    def test_duplicate_attribute_value_rejected(self, grey, color_attr):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AttributeValue.objects.create(attribute=color_attr, name="Grey")

    def test_same_value_name_allowed_for_other_attribute(self, grey, size_attr):
        value = AttributeValue.objects.create(attribute=size_attr, name="Grey")
        assert value.pk is not None


# ---------------------------------------------------------------------------
# ProductAttributeValue
# ---------------------------------------------------------------------------
class TestProductAttributeValue:
    def test_valid_color_configuration(self, product, color_attr, grey):
        pav = ProductAttributeValue(
            product=product,
            attribute=color_attr,
            attribute_value=grey,
            feature_image="https://res.cloudinary.com/demo/x.jpg",
        )
        pav.full_clean()
        pav.save()
        assert pav.pk is not None

    def test_color_without_feature_image_rejected(self, product, color_attr, grey):
        pav = ProductAttributeValue(
            product=product, attribute=color_attr, attribute_value=grey
        )
        with pytest.raises(ValidationError) as exc_info:
            pav.full_clean()
        assert "feature_image" in exc_info.value.message_dict

    def test_size_without_feature_image_allowed(self, product, size_attr, size_40):
        pav = ProductAttributeValue(
            product=product, attribute=size_attr, attribute_value=size_40
        )
        pav.full_clean()  # must not raise

    def test_attribute_value_mismatch_rejected(self, product, color_attr, size_40):
        pav = ProductAttributeValue(
            product=product,
            attribute=color_attr,
            attribute_value=size_40,
            feature_image="https://res.cloudinary.com/demo/x.jpg",
        )
        with pytest.raises(ValidationError) as exc_info:
            pav.full_clean()
        assert "attribute_value" in exc_info.value.message_dict

    def test_duplicate_product_attribute_value_rejected(
        self, product, color_attr, grey
    ):
        make_pav(product, color_attr, grey, image_url="https://res.cloudinary.com/demo/x.jpg")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_pav(
                    product, color_attr, grey,
                    image_url="https://res.cloudinary.com/demo/y.jpg",
                )

    def test_same_value_reusable_across_products(
        self, product, color_attr, grey, admin_user, category, product_model
    ):
        other = Product.objects.create(
            user=admin_user, name="Other Slippers", model=product_model,
            gender="WOMEN", category=category,
        )
        first = make_pav(product, color_attr, grey, image_url="https://res.cloudinary.com/demo/a.jpg")
        second = make_pav(other, color_attr, grey, image_url="https://res.cloudinary.com/demo/b.jpg")
        assert first.pk != second.pk

    def test_invalid_additional_images_rejected(self, product, size_attr, size_40):
        pav = make_pav(product, size_attr, size_40)
        row = ProductAttributeImage(product_attribute_value=pav, image="")
        with pytest.raises(ValidationError):
            row.full_clean()


# ---------------------------------------------------------------------------
# ProductVariant
# ---------------------------------------------------------------------------
class TestProductVariant:

    def test_create_variant(self, product, color_attr, size_attr, grey, size_40):
        grey_pav = make_pav(product, color_attr, grey, image_url="https://res.cloudinary.com/demo/x.jpg")
        pav_40 = make_pav(product, size_attr, size_40)
        variant = make_variant(
            product, "SKU-1", "100.00", [grey_pav, pav_40], special=True
        )
        assert variant.sku == "SKU-1"
        assert variant.is_special_edition is True
        assert variant.options.count() == 2

    def test_unique_sku(self, product_full):
        other_product = Product.objects.create(
            name="Other", model=product_full.model, gender="MEN", category=product_full.category
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductVariant.objects.create(
                    product=other_product,
                    sku="CELSI-GREY-40",
                    price="10.00",
                )

    def test_negative_price_rejected(self, product):
        variant = ProductVariant(
            product=product, sku="NEG-1", price="-5.00"
        )
        with pytest.raises(ValidationError) as exc_info:
            variant.full_clean()
        assert "price" in exc_info.value.message_dict

# ---------------------------------------------------------------------------
# ProductVariantOption
# ---------------------------------------------------------------------------
class TestProductVariantOption:
    def test_valid_option(self, product_full):
        variant = ProductVariant.objects.get(sku="CELSI-GREY-40")
        assert variant.option_value_ids() and len(variant.option_value_ids()) == 2

    def test_option_from_another_product_rejected(
        self, product_full, admin_user, category, product_model, color_attr, grey
    ):
        other = Product.objects.create(
            name="Other Slippers", model=product_model, gender="MEN", category=category
        )
        foreign_pav = make_pav(other, color_attr, grey, image_url="https://res.cloudinary.com/demo/z.jpg")
        variant = ProductVariant.objects.get(sku="CELSI-GREY-40")
        option = ProductVariantOption(variant=variant, product_attribute_value=foreign_pav)
        with pytest.raises(ValidationError) as exc_info:
            option.full_clean()
        assert "product_attribute_value" in exc_info.value.message_dict

    def test_duplicate_option_rejected(self, product_full):
        variant = ProductVariant.objects.get(sku="CELSI-GREY-40")
        existing = variant.options.first()
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductVariantOption.objects.create(
                    variant=variant,
                    product_attribute_value=existing.product_attribute_value,
                )

    def test_two_values_of_same_attribute_rejected(self, product_full):
        variant = ProductVariant.objects.get(sku="CELSI-GREY-40")
        blue_pav = ProductAttributeValue.objects.get(
            product=variant.product, attribute_value__name="Blue"
        )
        option = ProductVariantOption(variant=variant, product_attribute_value=blue_pav)
        with pytest.raises(ValidationError):
            option.full_clean()

    def test_pav_delete_protected_when_used_by_variant(self, product_full):
        grey_pav = ProductAttributeValue.objects.get(attribute_value__name="Grey")
        with pytest.raises(ProtectedError):
            grey_pav.delete()
