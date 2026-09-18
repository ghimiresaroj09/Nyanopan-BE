"""Catalog filters (public + admin)."""

import django_filters
from rest_framework.filters import OrderingFilter


class ProductOrderingFilter(OrderingFilter):
    """OrderingFilter with support for aliasing query params to annotations.

    ``?ordering=price`` sorts by the annotated ``min_price`` (cheapest active
    variant), so DRF's plain field validation keeps working.
    """

    FIELD_ALIASES = {"price": "min_price"}

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering
        aliased = []
        for term in ordering:
            descending = term.startswith("-")
            name = term[1:] if descending else term
            name = self.FIELD_ALIASES.get(name, name)
            aliased.append(f"-{name}" if descending else name)
        return aliased

from .models import (
    AttributeValue,
    Product,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantOption,
)


class ProductFilter(django_filters.FilterSet):
    """Public product filtering: category slug, gender, featured, price range."""

    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    gender = django_filters.ChoiceFilter(choices=Product._meta.get_field("gender").choices)
    is_featured = django_filters.BooleanFilter()
    min_price = django_filters.NumberFilter(method="filter_min_price")
    max_price = django_filters.NumberFilter(method="filter_max_price")

    class Meta:
        model = Product
        fields: list[str] = []

    def _active_variants(self, queryset):
        return queryset.filter(variants__is_active=True)

    def filter_min_price(self, queryset, name, value):
        return self._active_variants(queryset).filter(variants__price__gte=value).distinct()

    def filter_max_price(self, queryset, name, value):
        return self._active_variants(queryset).filter(variants__price__lte=value).distinct()


class ProductAdminFilter(ProductFilter):
    is_active = django_filters.BooleanFilter()


class AttributeValueAdminFilter(django_filters.FilterSet):
    attribute = django_filters.UUIDFilter(field_name="attribute_id")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = AttributeValue
        fields: list[str] = []


class ProductAttributeValueAdminFilter(django_filters.FilterSet):
    product = django_filters.UUIDFilter(field_name="product_id")
    attribute = django_filters.UUIDFilter(field_name="attribute_id")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = ProductAttributeValue
        fields: list[str] = []


class VariantAdminFilter(django_filters.FilterSet):
    product = django_filters.UUIDFilter(field_name="product_id")
    is_special_edition = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = ProductVariant
        fields: list[str] = []


class VariantOptionAdminFilter(django_filters.FilterSet):
    variant = django_filters.UUIDFilter(field_name="variant_id")
    product = django_filters.UUIDFilter(field_name="variant__product_id")

    class Meta:
        model = ProductVariantOption
        fields: list[str] = []
