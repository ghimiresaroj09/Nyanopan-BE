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


@extend_schema(
    auth=[],
    tags=["Public - Products"],
    description=(
        "List and retrieve products with filtering and sorting.\n\n"
        "**Filtering options:**\n"
        "- `category`: Filter by category slug (e.g., `?category=slippers`)\n"
        "- `gender`: Filter by gender (`MEN`, `WOMEN`, `UNISEX`, `KIDS`, `BABY`)\n"
        "- `usage_location`: Filter by usage location (`INSIDE`, `OUTSIDE`, `BOTH`)\n"
        "- `sole_type`: Filter by sole type (`LEATHER`, `RUBBER`)\n"
        "- `is_featured`: Filter featured products (`true`/`false`)\n"
        "- `min_price`: Filter by minimum price (e.g., `?min_price=1000`)\n"
        "- `max_price`: Filter by maximum price (e.g., `?max_price=5000`)\n\n"
        "**Sorting options (use `?ordering=`):**\n"
        "- `price_asc` or `price`: Low to High (by minimum price)\n"
        "- `price_desc` or `-price`: High to Low (by maximum price)\n"
        "- `name_asc` or `name`: A to Z\n"
        "- `name_desc` or `-name`: Z to A\n"
        "- `newest` or `-created_at`: Recently Added (default)\n"
        "- `oldest` or `created_at`: Previously Added\n\n"
        "**Search:**\n"
        "Use `?search=` to search across product name, description, model name, and category name.\n\n"
        "**Examples:**\n"
        "- `?gender=UNISEX&usage_location=INSIDE&ordering=price_asc`\n"
        "- `?category=slippers&sole_type=RUBBER&ordering=newest`\n"
        "- `?is_featured=true&min_price=1000&max_price=5000&ordering=name_asc`"
    ),
)
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
