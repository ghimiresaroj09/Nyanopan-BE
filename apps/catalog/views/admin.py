"""Admin catalog management endpoints (staff-only, JWT or session auth)."""

import json

from django.db.models import Count
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsAdminUser
from apps.common.responses import SuccessEnvelopeMixin

from ..filters import (
    AttributeValueAdminFilter,
    ProductAdminFilter,
    ProductAttributeValueAdminFilter,
    VariantAdminFilter,
    VariantOptionAdminFilter,
)
from ..models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttributeValue,
    ProductModel,
    ProductVariant,
    ProductVariantOption,
)
from ..selectors import pav_admin_queryset, product_admin_queryset, variant_admin_queryset
from ..serializers.admin import (
    AttributeAdminSerializer,
    AttributeValueAdminSerializer,
    AttributeValueBulkCreateSerializer,
    CategoryAdminSerializer,
    CategoryMultipartSerializer,
    ImageDeleteResponseSerializer,
    ImageDeleteSerializer,
    ImageUploadSerializer,
    ImageUploadResponseSerializer,
    ProductAdminResponseSerializer,
    ProductAdminWriteSerializer,
    ProductAttributeValueAdminSerializer,
    ProductMultipartSerializer,
    ProductAttributeValueMultipartSerializer,
    ProductModelAdminSerializer,
    VariantAdminSerializer,
    VariantOptionAdminSerializer,
)
from ..services.attributes import AttributeValueService
from ..services.categories import CategoryService
from ..services.images import ImageService
from ..services.products import ProductAttributeValueService, ProductService
from ..services.variants import VariantService


CATEGORY_JSON_EXAMPLE = OpenApiExample(
    "Category with image reference",
    value={
        "name": "Boots",
        "description": "Sturdy boots.",
        "image": {
            "url": "https://res.cloudinary.com/demo/image/upload/v1/shop/boots.jpg",
            "title": "Boots",
            "alt": "Boots",
        },
    },
    request_only=True,
    media_type="application/json",
)

PAV_JSON_EXAMPLE = OpenApiExample(
    "Value with image references",
    value={
        "product": "celsi-wool-felt-slippers",
        "attribute": "Color",
        "attribute_value": "Grey",
        "feature_image": {
            "public_id": "shop/grey-main",
            "title": "Grey",
            "alt": "Grey slippers",
        },
        "additional_images": [
            {
                "url": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-side.jpg",
                "title": "Side view",
            }
        ],
        "is_active": True,
    },
    request_only=True,
    media_type="application/json",
)

PRODUCT_JSON_EXAMPLE = OpenApiExample(
    "Product with nested values and variants (all-in-one)",
    description=(
        "Complete product creation including nested attribute values and variants. "
        "While possible to create everything at once, the recommended 3-step flow is:\n"
        "1. Create product info (this endpoint with basic fields only)\n"
        "2. Add variants via /productvarientvalues/{product_id}/\n"
        "3. Upload images via /productvarientimages/{product_id}/"
    ),
    value={
        "name": "Celsi Wool Felt Slippers",
        "model": "celsi",
        "gender": "UNISEX",
        "description": "Warm wool felt slippers.",
        "category": "slippers",
        "is_featured": True,
        "key_features": [{"title": "Sole", "value": "Rubber"}],
        "attribute_values": [
            {
                "key": "grey",
                "attribute": "Color",
                "attribute_value": "Grey",
                "feature_image": {
                    "public_id": "shop/grey-main",
                    "title": "Grey",
                    "alt": "Grey slippers",
                },
            },
            {
                "key": "40",
                "attribute": "Size",
                "attribute_value": "40",
            },
        ],
        "variants": [
            {
                "price": "5995.00",
                "options": [{"key": "grey"}, {"key": "40"}],
            }
        ],
    },
    request_only=True,
    media_type="application/json",
)

PRODUCT_STEP1_EXAMPLE = OpenApiExample(
    "Step 1: Product info only (recommended)",
    description=(
        "Recommended approach for Step 1: create the product with basic info only. "
        "Add variants in Step 2 and images in Step 3 using the returned product ID."
    ),
    value={
        "name": "Celsi Wool Felt Slippers",
        "model": "celsi",
        "gender": "UNISEX",
        "description": "Warm and comfortable wool felt slippers perfect for indoor use.",
        "category": "slippers",  # Can use category UUID or slug
        "is_active": True,
        "is_featured": True,
        "feature_image": {
            "url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "title": "Celsi Wool Felt Slippers",
            "alt": "Warm wool felt slippers main image",
        },
        "key_features": [
            {"title": "Material", "value": "100% Wool Felt"},
            {"title": "Sole", "value": "Rubber"},
            {"title": "Care", "value": "Spot clean only"},
        ],
    },
    request_only=True,
    media_type="application/json",
)

ATTRIBUTE_JSON_EXAMPLE = OpenApiExample(
    "Attribute with values",
    value={"name": "Color", "requires_image": True, "value": ["Grey", "Blue"]},
    request_only=True,
    media_type="application/json",
)

_HUMAN_KEYS_HELP = (
    "References accept UUIDs or human keys: category/model/product slugs, "
    "attribute names, value names (resolved within the attribute), "
    "and variant SKUs."
)

_DATA_URI_HELP = (
    'Image slots also accept inline uploads in JSON via {"file": '
    '"data:image/...;base64,..."}.'
)


class AdminViewSetMixin(SuccessEnvelopeMixin):
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({}, status=status.HTTP_200_OK)


def _decode_multipart_data(data, json_fields=(), list_fields=("additional_images",)):
    """Normalize multipart/form-data into a plain dict for serializers.

    Two fixes in one: QueryDict values collapse to last-value scalars (this
    also drops DRF's HTML-checkbox semantics, where a missing boolean reads as
    False), and ``json_fields`` entries are JSON-decoded. Repeated file parts
    listed in ``list_fields`` are preserved as lists.
    """
    multi = {}
    if hasattr(data, "getlist"):
        for field in list_fields:
            values = [value for value in data.getlist(field, []) if hasattr(value, "read")]
            if values:
                multi[field] = values
    if hasattr(data, "dict"):
        decoded = data.dict()
    elif hasattr(data, "get"):
        decoded = dict(data)
    else:
        return data
    for field in json_fields:
        value = decoded.get(field)
        if isinstance(value, str) and value.strip():
            try:
                decoded[field] = json.loads(value)
            except ValueError:
                raise ValidationError({field: ["Must be valid JSON when using multipart/form-data."]})
    decoded.update(multi)
    return decoded


class MultipartDataMixin:
    """Decode multipart requests (nested JSON + file parts) for image writes."""

    multipart_json_fields: tuple = ()

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get("data")
        request = getattr(self, "request", None)
        content_type = getattr(request, "content_type", "") or ""
        if data is not None and content_type.startswith("multipart/"):
            kwargs["data"] = _decode_multipart_data(data, self.multipart_json_fields)
        return super().get_serializer(*args, **kwargs)


@extend_schema_view(
    create=extend_schema(
        request={
            "application/json": CategoryAdminSerializer,
            "multipart/form-data": CategoryMultipartSerializer,
        },
        description="Create a category. Send application/json with an `image` "
        "{url|name|public_id, ...} object (or null to leave blank), or "
        "multipart/form-data with a binary `image` file. " + _DATA_URI_HELP,
        examples=[CATEGORY_JSON_EXAMPLE],
    ),
    update=extend_schema(
        request={
            "application/json": CategoryAdminSerializer,
            "multipart/form-data": CategoryMultipartSerializer,
        },
        description="Replace a category. Send application/json with an `image` "
        "{url|name|public_id, ...} object (or null to clear the image), or "
        "multipart/form-data with a binary `image` file. " + _DATA_URI_HELP,
        examples=[CATEGORY_JSON_EXAMPLE],
    ),
    partial_update=extend_schema(
        request={
            "application/json": CategoryAdminSerializer,
            "multipart/form-data": CategoryMultipartSerializer,
        },
        description="Update a category. Send application/json with an `image` "
        "{url|name|public_id, ...} object (or null to clear the image), or "
        "multipart/form-data with a binary `image` file. " + _DATA_URI_HELP,
        examples=[CATEGORY_JSON_EXAMPLE],
    ),
)
@extend_schema(tags=["Admin - Categories"])
class AdminCategoryViewSet(MultipartDataMixin, AdminViewSetMixin, ModelViewSet):
    queryset = (
        Category.objects.annotate(product_count=Count("products")).order_by("name")
    )
    serializer_class = CategoryAdminSerializer
    search_fields = ["name", "description", "slug"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["name"]
    filterset_fields = ["is_active"]

    def perform_destroy(self, instance):
        CategoryService.delete_category(category=instance)


@extend_schema(tags=["Admin - Product Models"])
class AdminProductModelViewSet(AdminViewSetMixin, ModelViewSet):
    queryset = (
        ProductModel.objects.annotate(product_count=Count("products")).order_by("name")
    )
    serializer_class = ProductModelAdminSerializer
    search_fields = ["name", "description", "slug"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["name"]
    filterset_fields = ["is_active"]


@extend_schema_view(
    create=extend_schema(
        description="Create an attribute, optionally with nested `value` names created in the same request.",
        examples=[ATTRIBUTE_JSON_EXAMPLE],
    ),
    update=extend_schema(
        description="Replace an attribute. Nested `value` names are ensured to exist (existing names are left untouched).",
        examples=[ATTRIBUTE_JSON_EXAMPLE],
    ),
    partial_update=extend_schema(
        description="Update an attribute. Nested `value` names are ensured to exist (existing names are left untouched).",
        examples=[ATTRIBUTE_JSON_EXAMPLE],
    ),
)
@extend_schema(tags=["Admin - Attributes"])
class AdminAttributeViewSet(AdminViewSetMixin, ModelViewSet):
    queryset = (
        Attribute.objects.annotate(values_count=Count("values"))
        .prefetch_related("values")
        .order_by("name")
    )
    serializer_class = AttributeAdminSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["name"]
    filterset_fields = ["is_active", "requires_image"]

    def _read_response(self, instance, *, status_code):
        fresh = self.get_queryset().get(pk=instance.pk)
        serializer = self.get_serializer(fresh)
        return Response(serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return self._read_response(instance, status_code=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._read_response(instance, status_code=status.HTTP_200_OK)


@extend_schema(tags=["Admin - Attribute Values"])
class AdminAttributeValueViewSet(AdminViewSetMixin, ModelViewSet):
    queryset = AttributeValue.objects.select_related("attribute").order_by(
        "attribute__name", "name"
    )
    serializer_class = AttributeValueAdminSerializer
    filterset_class = AttributeValueAdminFilter
    search_fields = ["name", "attribute__name"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["attribute__name", "name"]

    @extend_schema(
        request=AttributeValueBulkCreateSerializer,
        responses={201: AttributeValueAdminSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Bulk values",
                value={"attribute": "Color", "value": ["Red", "Black", "Blue"]},
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create_values(self, request, *args, **kwargs):
        """Create many values for one attribute in a single atomic request."""
        return self._bulk_create_response(request)

    def _bulk_create_response(self, request):
        input_serializer = AttributeValueBulkCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        values = AttributeValueService.bulk_create(
            attribute=input_serializer.validated_data["attribute"],
            names=input_serializer.validated_data["value"],
        )
        count = len(values)
        self.success_message = (
            f"{count} attribute value{'s' if count != 1 else ''} created successfully."
        )
        output = AttributeValueAdminSerializer(values, many=True)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description=(
            "Create one attribute value (`{attribute, name}`) or many at once "
            "(`{attribute, value: [...]}`); the bulk shape is identical to "
            "POST .../attribute-values/bulk/."
        ),
        examples=[
            OpenApiExample(
                "Single value",
                value={"attribute": "Color", "name": "Red"},
                request_only=True,
            ),
            OpenApiExample(
                "Bulk values",
                value={"attribute": "Color", "value": ["Red", "Black", "Blue"]},
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        data = request.data if isinstance(request.data, dict) else {}
        has_name = "name" in data
        has_value = "value" in data
        if has_name and has_value:
            raise ValidationError("Provide either 'name' or 'value', not both.")
        if has_value:
            if not isinstance(data.get("value"), list):
                raise ValidationError({"value": ["Must be an array of strings."]})
            return self._bulk_create_response(request)
        return super().create(request, *args, **kwargs)


@extend_schema_view(
    create=extend_schema(
        request={
            "application/json": ProductAttributeValueAdminSerializer,
            "multipart/form-data": ProductAttributeValueMultipartSerializer,
        },
        description="Create a product attribute value. Send application/json with "
        "{url|name|public_id, ...} image objects (null clears a single image), or "
        "multipart/form-data with binary `feature_image` / `additional_images` "
        "files (repeat the part for multiple images). "
        + _HUMAN_KEYS_HELP
        + " "
        + _DATA_URI_HELP,
        examples=[PAV_JSON_EXAMPLE],
    ),
    update=extend_schema(
        request={
            "application/json": ProductAttributeValueAdminSerializer,
            "multipart/form-data": ProductAttributeValueMultipartSerializer,
        },
        description="Replace a product attribute value. Send application/json with "
        "{url|name|public_id, ...} image objects (null clears a single image), or "
        "multipart/form-data with binary `feature_image` / `additional_images` "
        "files (repeat the part for multiple images). "
        + _HUMAN_KEYS_HELP
        + " "
        + _DATA_URI_HELP,
        examples=[PAV_JSON_EXAMPLE],
    ),
    partial_update=extend_schema(
        request={
            "application/json": ProductAttributeValueAdminSerializer,
            "multipart/form-data": ProductAttributeValueMultipartSerializer,
        },
        description="Update a product attribute value. Send application/json with "
        "{url|name|public_id, ...} image objects (null clears a single image), or "
        "multipart/form-data with binary `feature_image` / `additional_images` "
        "files (repeat the part for multiple images). "
        + _HUMAN_KEYS_HELP
        + " "
        + _DATA_URI_HELP,
        examples=[PAV_JSON_EXAMPLE],
    ),
)
@extend_schema(tags=["Admin - Product Attribute Values"])
class AdminProductAttributeValueViewSet(MultipartDataMixin, AdminViewSetMixin, ModelViewSet):
    queryset = pav_admin_queryset()
    serializer_class = ProductAttributeValueAdminSerializer
    filterset_class = ProductAttributeValueAdminFilter
    search_fields = [
        "product__name",
        "attribute__name",
        "attribute_value__name",
    ]
    ordering_fields = ["created_at", "is_active"]
    ordering = ["created_at", "id"]

    def perform_destroy(self, instance):
        ProductAttributeValueService.delete_pav(pav=instance)


@extend_schema(tags=["Admin - Variants"])
class AdminVariantViewSet(AdminViewSetMixin, ModelViewSet):
    queryset = variant_admin_queryset()
    serializer_class = VariantAdminSerializer
    filterset_class = VariantAdminFilter
    search_fields = ["sku", "product__name"]
    ordering_fields = ["price", "sku", "created_at", "is_active"]
    ordering = ["created_at", "id"]


@extend_schema(tags=["Admin - Variant Options"])
class AdminVariantOptionViewSet(AdminViewSetMixin, ModelViewSet):
    queryset = (
        ProductVariantOption.objects.select_related(
            "variant",
            "variant__product",
            "product_attribute_value__attribute",
            "product_attribute_value__attribute_value",
        ).order_by("id")
    )
    serializer_class = VariantOptionAdminSerializer
    filterset_class = VariantOptionAdminFilter
    ordering_fields = ["created_at"]
    ordering = ["created_at", "id"]

    def perform_destroy(self, instance):
        VariantService.remove_option(option=instance)


_PRODUCT_MULTIPART_HELP = (
    "Send application/json with image slots as {url|name|public_id, ...} objects "
    "multipart/form-data: nested attribute_values/variants/key_features go in "
    'as JSON-encoded strings, files as parts, and image slots reference them '
    'via {"file": "<part-name>"}. Example: '
    "-F attribute_values='[{\"key\": \"grey\", \"attribute\": \"<uuid>\", "
    '"attribute_value\": \"<uuid>\", \"feature_image\": {\"file\": \"grey-img\"}}]\' '
    "-F grey-img=@grey.png"
)


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="List products with their info, values and variants.",
    ),
    retrieve=extend_schema(
        summary="Get product info",
        description="Get one product with its info, values and variants.",
    ),
    destroy=extend_schema(
        summary="Delete product",
        description="Delete a product with its values, variants and images.",
    ),
)
@extend_schema(tags=["Product 1/3 - Info"])
class AdminProductViewSet(MultipartDataMixin, AdminViewSetMixin, ModelViewSet):
    use_status_envelope = True
    filterset_class = ProductAdminFilter
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "created_at", "updated_at", "is_active", "is_featured"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return product_admin_queryset()

    def get_success_message(self, request):
        messages = {
            "list": "Products retrieved successfully.",
            "retrieve": "Product retrieved successfully.",
            "create": "Product created successfully.",
            "update": "Product updated successfully.",
            "partial_update": "Product updated successfully.",
            "destroy": "Product deleted successfully.",
        }
        return messages.get(self.action, super().get_success_message(request))

    multipart_json_fields = ("attribute_values", "variants", "key_features")

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ProductAdminWriteSerializer
        return ProductAdminResponseSerializer

    def _read_response(self, instance, *, status_code):
        fresh = self.get_queryset().get(pk=instance.pk)
        serializer = ProductAdminResponseSerializer(fresh, context=self.get_serializer_context())
        return Response(serializer.data, status=status_code)

    @extend_schema(
        request={
            "application/json": ProductAdminWriteSerializer,
            "multipart/form-data": ProductMultipartSerializer,
        },
        responses={201: ProductAdminResponseSerializer},
        summary="Step 1: Add product info",
        description=(
            "Step 1 of the product flow: create the product with its "
            "basic info (name, category, model, description, key features).\n\n"
            "**Recommended flow:**\n"
            "1. Use this endpoint to create product with basic info only\n"
            "2. Note the returned `product.id`\n"
            "3. Use that ID in Step 2 to add variants and prices\n"
            "4. Use that ID in Step 3 to upload images\n\n"
            "**Advanced:** Nested values/variants are also accepted here for "
            "all-in-one creation, but the guided 3-step flow is recommended. "
            + _PRODUCT_MULTIPART_HELP
            + " "
            + _HUMAN_KEYS_HELP
            + " "
            + _DATA_URI_HELP
        ),
        examples=[PRODUCT_STEP1_EXAMPLE, PRODUCT_JSON_EXAMPLE],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return self._read_response(instance, status_code=status.HTTP_201_CREATED)

    @extend_schema(
        request={
            "application/json": ProductAdminWriteSerializer,
            "multipart/form-data": ProductMultipartSerializer,
        },
        responses={200: ProductAdminResponseSerializer},
        summary="Replace product info",
        description="Replace a product with nested values and variants. "
        + _PRODUCT_MULTIPART_HELP
        + " "
        + _HUMAN_KEYS_HELP
        + " "
        + _DATA_URI_HELP,
        examples=[PRODUCT_JSON_EXAMPLE],
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._read_response(instance, status_code=status.HTTP_200_OK)

    @extend_schema(
        request={
            "application/json": ProductAdminWriteSerializer,
            "multipart/form-data": ProductMultipartSerializer,
        },
        responses={200: ProductAdminResponseSerializer},
        summary="Update product info",
        description="Partially update a product with nested values and variants. "
        + _PRODUCT_MULTIPART_HELP
        + " "
        + _HUMAN_KEYS_HELP
        + " "
        + _DATA_URI_HELP,
        examples=[PRODUCT_JSON_EXAMPLE],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        ProductService.delete_product(product=instance)


@extend_schema(tags=["Admin - Images"], responses={201: ImageUploadResponseSerializer})
class ImageUploadView(AdminViewSetMixin, GenericAPIView):
    """Upload an image file and get back its URL + public_id.

    Stored on Cloudinary, or under local media/ when Cloudinary is not
    enabled. Use the returned reference inside category /
    product-attribute payloads.
    """

    serializer_class = ImageUploadSerializer
    success_message = "Image uploaded successfully."
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ImageService.upload_image(
            serializer.validated_data["image"],
            folder=serializer.validated_data.get("folder") or None,
        )
        if result["url"].startswith("/"):
            # Filesystem fallback: return an absolute URL like Cloudinary does.
            result["url"] = request.build_absolute_uri(result["url"])
        return Response(result, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Admin - Images"], responses={200: ImageDeleteResponseSerializer})
class ImageDeleteView(AdminViewSetMixin, GenericAPIView):
    """Delete an uploaded asset by public_id (for manually uploaded files)."""

    serializer_class = ImageDeleteSerializer
    success_message = "Image deleted successfully."

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deleted = ImageService.delete_image(serializer.validated_data["public_id"])
        return Response({"deleted": deleted}, status=status.HTTP_200_OK)
