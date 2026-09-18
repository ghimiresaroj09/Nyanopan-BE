"""Public read-only catalog endpoints. Active records only, no auth required."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.common.responses import SuccessEnvelopeMixin

from ..filters import ProductFilter, ProductOrderingFilter
from ..selectors import (
    attribute_public_queryset,
    category_public_queryset,
    product_detail_queryset,
    product_list_queryset,
    product_model_public_queryset,
)
from ..serializers.public import (
    AttributePublicSerializer,
    CategoryPublicSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductModelPublicSerializer,
)


@extend_schema(auth=[], tags=["Public - Categories"])
class CategoryPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    queryset = category_public_queryset()
    serializer_class = CategoryPublicSerializer
    success_message = "Categories retrieved successfully."
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


@extend_schema(auth=[], tags=["Public - Product Models"])
class ProductModelPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    queryset = product_model_public_queryset()
    serializer_class = ProductModelPublicSerializer
    success_message = "Product models retrieved successfully."
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


@extend_schema(auth=[], tags=["Public - Attributes"])
class AttributePublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    queryset = attribute_public_queryset()
    serializer_class = AttributePublicSerializer
    success_message = "Attributes retrieved successfully."
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


@extend_schema(auth=[], tags=["Public - Products"])
class ProductPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    success_message = "Products retrieved successfully."
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, ProductOrderingFilter]
    search_fields = ["name", "description", "model__name", "category__name"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.action == "retrieve":
            return product_detail_queryset()
        return product_list_queryset()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
