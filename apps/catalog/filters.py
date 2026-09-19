"""Catalog filters (public + admin)."""

import django_filters
from rest_framework.filters import OrderingFilter


class ProductOrderingFilter(OrderingFilter):
    """OrderingFilter with support for aliasing query params to annotations and custom sort options.

    ``?ordering=price`` sorts by the annotated ``min_price`` (cheapest active variant).
    
    Supported ordering options:
    - price: Low to High (by min_price)
    - -price: High to Low (by max_price)
    - name: A to Z
    - -name: Z to A
    - created_at: Previously Added (oldest first)
    - -created_at: Recently Added (newest first, default)
    
    Friendly aliases:
    - price_asc: Low to High
    - price_desc: High to Low
    - name_asc: A to Z
    - name_desc: Z to A
    - newest: Recently Added
    - oldest: Previously Added
    """

    FIELD_ALIASES = {
        "price": "min_price",
        # Friendly aliases for frontend
        "price_asc": "min_price",
        "price_desc": "-max_price",
        "name_asc": "name",
        "name_desc": "-name",
        "newest": "-created_at",
        "oldest": "created_at",
    }

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering
        aliased = []
        for term in ordering:
            # Check if term is a friendly alias first
            if term in self.FIELD_ALIASES:
                alias_value = self.FIELD_ALIASES[term]
                aliased.append(alias_value)
                continue
                
            # Handle standard ordering with potential aliases
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
    """Public product filtering: category slug, gender, usage_location, sole_type, featured, price range."""

    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    gender = django_filters.ChoiceFilter(choices=Product._meta.get_field("gender").choices)
    usage_location = django_filters.ChoiceFilter(
        field_name="usage_location",
        choices=Product._meta.get_field("usage_location").choices,
        help_text="Filter by usage location: INSIDE, OUTSIDE, or BOTH"
    )
    sole_type = django_filters.ChoiceFilter(
        field_name="sole_type",
        choices=Product._meta.get_field("sole_type").choices,
        help_text="Filter by sole type: LEATHER or RUBBER"
    )
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
