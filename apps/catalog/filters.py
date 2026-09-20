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
    """Public product filtering: category slug, model, gender, usage_location, sole_type, featured, price range, attribute values.
    
    Supports two attribute filtering formats:
    1. Name-based: ?attribute=color:grey&attribute=size:large
    2. ID-based (frontend): ?attribute_{attr_id}={value_id}
    """

    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    model = django_filters.CharFilter(field_name="model__slug", lookup_expr="iexact", help_text="Filter by product model slug (e.g., celsi-wool-felt)")
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
    
    # Attribute value filters - support multiple values for same attribute
    attribute = django_filters.CharFilter(
        method="filter_by_attribute",
        help_text="Filter by attribute name and value name (e.g., ?attribute=color:grey or ?attribute=Color:Grey)"
    )

    class Meta:
        model = Product
        fields: list[str] = []

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
        # Store request for later use in qs property
        self._request = request

    def _active_variants(self, queryset):
        return queryset.filter(variants__is_active=True)

    def filter_min_price(self, queryset, name, value):
        return self._active_variants(queryset).filter(variants__price__gte=value).distinct()

    def filter_max_price(self, queryset, name, value):
        return self._active_variants(queryset).filter(variants__price__lte=value).distinct()
    
    def filter_by_attribute(self, queryset, name, value):
        """Filter products by attribute value name.
        
        This method is called once for EACH attribute parameter.
        When multiple attributes are provided, django-filters calls this method
        multiple times, each time passing the already-filtered queryset.
        
        Supports multiple formats:
        - ?attribute=color:grey (single value)
        - ?attribute=color:grey&attribute=color:black (multiple values for same attribute - OR via separate queries)
        - ?attribute=color:grey&attribute=size:large (different attributes - AND via chaining)
        
        Format: attribute_name:value_name (case-insensitive)
        
        Examples:
        - attribute=color:grey or attribute=Color:Grey
        - attribute=size:large or attribute=Size:Large
        """
        if not value or ":" not in value:
            return queryset
        
        try:
            attribute_name, value_name = value.split(":", 1)
            attribute_name = attribute_name.strip()
            value_name = value_name.strip()
            
            if not attribute_name or not value_name:
                return queryset
            
            # Filter products that have this attribute value (case-insensitive)
            return queryset.filter(
                attribute_values__attribute__name__iexact=attribute_name,
                attribute_values__attribute_value__name__iexact=value_name,
                attribute_values__is_active=True
            ).distinct()
        except (ValueError, AttributeError):
            # Invalid format, return unfiltered
            return queryset
    
    @property
    def qs(self):
        """Override to handle dynamic attribute_{id}={value_id} parameters from frontend."""
        queryset = super().qs
        
        # Get request data
        request_data = None
        if self._request:
            request_data = self._request.GET
        elif self.data:
            request_data = self.data
        
        if not request_data:
            return queryset
        
        # Handle dynamic attribute_<uuid>=<uuid> parameters from frontend
        # Format: ?attribute_af4f4dfb-fe59-4d2f-a5b2-e9d0a697f164=332dd17b-7d92-417f-b5b4-8169d23fb417
        # This allows filtering by: attribute ID + value ID (used by frontend)
        for param_name in request_data.keys():
            if param_name.startswith('attribute_'):
                try:
                    # Extract attribute ID from parameter name
                    attribute_id = param_name.replace('attribute_', '')
                    
                    # Validate it looks like a UUID (simple check)
                    if len(attribute_id) == 36 and attribute_id.count('-') == 4:
                        # Get value IDs (can be multiple for OR logic)
                        value_ids = request_data.getlist(param_name)
                        
                        if value_ids:
                            # Filter products that have ANY of these attribute values
                            # Multiple values = OR logic for the same attribute
                            from django.db.models import Q
                            q_objects = Q()
                            for value_id in value_ids:
                                value_id = value_id.strip()
                                if value_id:
                                    q_objects |= Q(
                                        attribute_values__attribute_id=attribute_id,
                                        attribute_values__attribute_value_id=value_id,
                                        attribute_values__is_active=True
                                    )
                            
                            if q_objects:
                                queryset = queryset.filter(q_objects)
                except (ValueError, AttributeError):
                    # Invalid UUID format, skip this parameter
                    continue
        
        return queryset.distinct()


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
