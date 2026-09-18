"""Read-query helpers. All public selectors return active records only and
prefetch relations to avoid N+1 queries."""

from django.db.models import Count, Max, Min, Prefetch, Q

from .models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttributeValue,
    ProductModel,
    ProductVariant,
    ProductVariantOption,
)

_ACTIVE_VARIANT_Q = Q(variants__is_active=True)


def active_product_queryset():
    """Products visible publicly: active products in active categories."""
    return Product.objects.filter(is_active=True, category__is_active=True)


def _public_pav_queryset():
    return (
        ProductAttributeValue.objects.filter(
            is_active=True,
            attribute__is_active=True,
            attribute_value__is_active=True,
        )
        .select_related("attribute", "attribute_value")
        .order_by("created_at", "id")
    )


def _public_variant_queryset():
    option_queryset = (
        ProductVariantOption.objects.select_related(
            "product_attribute_value__attribute",
            "product_attribute_value__attribute_value",
        ).order_by("created_at", "id")
    )
    return (
        ProductVariant.objects.filter(is_active=True)
        .prefetch_related(Prefetch("options", queryset=option_queryset))
        .order_by("created_at", "id")
    )


def product_list_queryset():
    """Optimized queryset for the public product list endpoint."""
    image_queryset = (
        _public_pav_queryset()
        .exclude(feature_image="")
        .order_by("-attribute__requires_image", "created_at", "id")
    )
    price_variant_queryset = (
        ProductVariant.objects.filter(is_active=True)
        .order_by("price", "created_at", "id")
    )
    return (
        active_product_queryset()
        .select_related("category", "model")
        .prefetch_related(
            Prefetch("attribute_values", queryset=image_queryset, to_attr="prefetched_images"),
            Prefetch("variants", queryset=price_variant_queryset, to_attr="prefetched_variants"),
        )
        .annotate(
            min_price=Min("variants__price", filter=Q(variants__is_active=True)),
            max_price=Max("variants__price", filter=Q(variants__is_active=True)),
        )
    )


def product_detail_queryset():
    """Optimized queryset for the public product detail endpoint."""
    return (
        active_product_queryset()
        .select_related("category", "model")
        .prefetch_related(
            Prefetch(
                "attribute_values",
                queryset=_public_pav_queryset().prefetch_related("additional_images"),
                to_attr="prefetched_pavs",
            ),
            Prefetch("variants", queryset=_public_variant_queryset(), to_attr="prefetched_variants"),
        )
    )


def category_public_queryset():
    return (
        Category.objects.filter(is_active=True)
        .annotate(
            product_count=Count("products", filter=Q(products__is_active=True))
        )
        .order_by("name")
    )


def product_model_public_queryset():
    return ProductModel.objects.filter(is_active=True).order_by("name")


def attribute_public_queryset():
    values_queryset = AttributeValue.objects.filter(is_active=True).order_by("name")
    return (
        Attribute.objects.filter(is_active=True)
        .prefetch_related(Prefetch("values", queryset=values_queryset, to_attr="active_values"))
        .order_by("name")
    )


def product_admin_queryset():
    """Optimized queryset for admin product retrieve/update responses."""
    return (
        Product.objects.select_related("category", "model", "user")
        .prefetch_related(
            Prefetch(
                "attribute_values",
                queryset=ProductAttributeValue.objects.select_related(
                    "attribute", "attribute_value"
                )
                .prefetch_related("additional_images")
                .order_by("created_at", "id"),
            ),
            Prefetch(
                "variants",
                queryset=ProductVariant.objects
                .prefetch_related(
                    Prefetch(
                        "options",
                        queryset=ProductVariantOption.objects.select_related(
                            "product_attribute_value__attribute",
                            "product_attribute_value__attribute_value",
                        ).order_by("created_at", "id"),
                    )
                )
                .order_by("created_at", "id"),
            ),
        )
        .order_by("-created_at")
    )


def variant_admin_queryset():
    return (
        ProductVariant.objects.select_related("product")
        .prefetch_related(
            Prefetch(
                "options",
                queryset=ProductVariantOption.objects.select_related(
                    "product_attribute_value__attribute",
                    "product_attribute_value__attribute_value",
                ).order_by("created_at", "id"),
            )
        )
        .order_by("created_at", "id")
    )


def pav_admin_queryset():
    return (
        ProductAttributeValue.objects.select_related(
            "product", "attribute", "attribute_value"
        )
        .prefetch_related("additional_images")
        .order_by("created_at", "id")
    )
