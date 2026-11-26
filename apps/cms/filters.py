"""Filters for public and admin blog endpoints."""

import django_filters

from .models import Blog


class BlogFilter(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name="category_id")
    min_views = django_filters.NumberFilter(field_name="views", lookup_expr="gte")
    max_views = django_filters.NumberFilter(field_name="views", lookup_expr="lte")
    is_featured = django_filters.BooleanFilter()
    is_published = django_filters.BooleanFilter()

    class Meta:
        model = Blog
        fields = ["category", "min_views", "max_views", "is_featured", "is_published"]
