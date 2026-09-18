"""Shared pytest fixtures (database + API clients + catalog builders)."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

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
from apps.catalog.services.images import ImageService

User = get_user_model()

GREY_IMAGE = "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-main.jpg"
BLUE_IMAGE = "https://res.cloudinary.com/demo/image/upload/v1/shop/blue-main.jpg"
GREY_NAME = "shop/grey-main"
BLUE_NAME = "shop/blue-main"


def success_data(response, status_code=200):
    """Assert the ``{success, message, data}`` envelope; return inner ``data``."""
    assert response.status_code == status_code, response.data
    assert response.data["success"] is True
    assert isinstance(response.data.get("message"), str) and response.data["message"]
    assert "data" in response.data
    return response.data["data"]


def status_data(response, status_code=200):
    """Assert the ``{status, message, statusCode, data}`` envelope; return ``data``."""
    assert response.status_code == status_code, response.data
    assert response.data["status"] == "success"
    assert isinstance(response.data.get("message"), str) and response.data["message"]
    assert response.data["statusCode"] == status_code, response.data
    assert "data" in response.data
    return response.data["data"]


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com", password="admin-pass-123", is_staff=True
    )


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(email="bob@example.com", password="bob-pass-123")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def plain_client(plain_user):
    client = APIClient()
    client.force_authenticate(user=plain_user)
    return client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Slippers", description="Comfy slippers")


@pytest.fixture
def inactive_category(db):
    return Category.objects.create(name="Archived", is_active=False)


@pytest.fixture
def product_model(db):
    return ProductModel.objects.create(name="Celsi")


@pytest.fixture
def color_attr(db):
    return Attribute.objects.create(name="Color", requires_image=True)


@pytest.fixture
def size_attr(db):
    return Attribute.objects.create(name="Size")


@pytest.fixture
def grey(color_attr):
    return AttributeValue.objects.create(attribute=color_attr, name="Grey")


@pytest.fixture
def blue(color_attr):
    return AttributeValue.objects.create(attribute=color_attr, name="Blue")


@pytest.fixture
def size_40(size_attr):
    return AttributeValue.objects.create(attribute=size_attr, name="40")


@pytest.fixture
def size_41(size_attr):
    return AttributeValue.objects.create(attribute=size_attr, name="41")


@pytest.fixture
def product(db, admin_user, category, product_model):
    return Product.objects.create(
        user=admin_user,
        name="Celsi Wool Felt Slippers",
        model=product_model,
        gender="UNISEX",
        description="Warm wool felt slippers.",
        general_information="Handmade in Nepal.",
        materials_used="Wool felt, rubber sole.",
        category=category,
        is_featured=True,
        key_features=[
            {"title": "Upper Material", "value": "Wool Felt"},
            {"title": "Sole", "value": "Rubber"},
        ],
    )


def make_pav(product, attribute, value, *, image_url="", public_id="", image_name="",
           additional_images=(), **extra):
    """Create a PAV storing the image *name* (URL/public_id inputs converted)."""
    pav = ProductAttributeValue.objects.create(
        product=product,
        attribute=attribute,
        attribute_value=value,
        feature_image=image_name or public_id or ImageService.reference_name_from_url(image_url),
        feature_image_title=extra.pop("title", ""),
        feature_image_caption=extra.pop("caption", ""),
        feature_image_alt=extra.pop("alt", ""),
        **extra,
    )
    for order, item in enumerate(additional_images):
        ref = (
            item.get("name", "")
            or item.get("public_id", "")
            or ImageService.reference_name_from_url(item.get("url", ""))
        )
        ProductAttributeImage.objects.create(
            product_attribute_value=pav,
            image=ref,
            title=item.get("title", "") or "",
            caption=item.get("caption", "") or "",
            alt=item.get("alt", "") or "",
            sort_order=item.get("sort_order", order),
        )
    return pav


def make_variant(product, sku, price, pavs, *, special=False, **extra):
    variant = ProductVariant.objects.create(
        product=product,
        sku=sku,
        price=price,
        is_special_edition=special,
        **extra,
    )
    for pav in pavs:
        ProductVariantOption.objects.create(variant=variant, product_attribute_value=pav)
    return variant


@pytest.fixture
def product_full(
    product, color_attr, size_attr, grey, blue, size_40, size_41
):
    """Product with Grey/Blue x 40/41 configuration and three variants."""
    grey_pav = make_pav(
        product, color_attr, grey,
        image_url=GREY_IMAGE, public_id="shop/grey-main",
        title="Grey Celsi Slippers", caption="Grey wool felt slippers", alt="Grey slippers",
        additional_images=[
            {
                "url": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-side.jpg",
                "public_id": "shop/grey-side",
                "title": "Side view",
                "caption": "",
                "alt": "Grey slippers side view",
            }
        ],
    )
    blue_pav = make_pav(
        product, color_attr, blue,
        image_url=BLUE_IMAGE, public_id="shop/blue-main",
        title="Blue Celsi Slippers", alt="Blue slippers",
    )
    pav_40 = make_pav(product, size_attr, size_40)
    pav_41 = make_pav(product, size_attr, size_41)
    make_variant(product, "CELSI-GREY-40", "5995.00", [grey_pav, pav_40])
    make_variant(product, "CELSI-GREY-41", "5995.00", [grey_pav, pav_41])
    make_variant(
        product, "CELSI-BLUE-40", "6495.00", [blue_pav, pav_40], special=True
    )
    return product
