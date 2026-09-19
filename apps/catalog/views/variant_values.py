"""Tab-2 endpoint: POST/PATCH /api/v1/productvarientvalues/{product_id}/.

Mounted outside ``/api/v1/admin/`` (exact frontend path) but staff-only like
every other write endpoint.
"""

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.responses import SuccessEnvelopeMixin

from ..models import Product
from ..serializers.variant_values import (
    ProductVariantValuesPatchSerializer,
    ProductVariantValuesResponseSerializer,
    ProductVariantValuesSerializer,
)
from ..services.variant_values import ProductVariantValuesService


# Step 2 examples
STEP2_POST_EXAMPLE = OpenApiExample(
    "Create variants with attributes and prices",
    description=(
        "Example showing how to create product variants by defining the attribute "
        "palette (Color + Size) and the generated variant combinations with prices."
    ),
    value={
        "attributes": [
            {
                "attribute": "550e8400-e29b-41d4-a716-446655440001",  # Color attribute UUID
                "options": [
                    "550e8400-e29b-41d4-a716-446655440011",  # Grey value UUID
                    "550e8400-e29b-41d4-a716-446655440012",  # Blue value UUID
                ],
            },
            {
                "attribute": "550e8400-e29b-41d4-a716-446655440002",  # Size attribute UUID
                "options": [
                    "550e8400-e29b-41d4-a716-446655440021",  # 40 value UUID
                    "550e8400-e29b-41d4-a716-446655440022",  # 41 value UUID
                ],
            },
        ],
        "generatedVarients": [
            {
                "sku": "CELSI-GREY-40",
                "name": "Grey - Size 40",
                "price": "5995.00",
                "is_active": True,
                "is_special_edition": False,
                "product": "550e8400-e29b-41d4-a716-446655440000",  # Product UUID from step 1
                "optionIds": [
                    "550e8400-e29b-41d4-a716-446655440011",  # Grey
                    "550e8400-e29b-41d4-a716-446655440021",  # 40
                ],
                "attributes": [
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440001",  # Color
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440011"],  # Grey
                    },
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440002",  # Size
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440021"],  # 40
                    },
                ],
            },
            {
                "sku": "CELSI-GREY-41",
                "name": "Grey - Size 41",
                "price": "5995.00",
                "is_active": True,
                "is_special_edition": False,
                "product": "550e8400-e29b-41d4-a716-446655440000",
                "optionIds": [
                    "550e8400-e29b-41d4-a716-446655440011",  # Grey
                    "550e8400-e29b-41d4-a716-446655440022",  # 41
                ],
                "attributes": [
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440001",
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440011"],
                    },
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440002",
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440022"],
                    },
                ],
            },
            {
                "sku": "CELSI-BLUE-40",
                "name": "Blue - Size 40",
                "price": "6495.00",
                "is_active": True,
                "is_special_edition": False,
                "product": "550e8400-e29b-41d4-a716-446655440000",
                "optionIds": [
                    "550e8400-e29b-41d4-a716-446655440012",  # Blue
                    "550e8400-e29b-41d4-a716-446655440021",  # 40
                ],
                "attributes": [
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440001",
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440012"],
                    },
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440002",
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440021"],
                    },
                ],
            },
            {
                "sku": "CELSI-BLUE-41",
                "name": "Blue - Size 41",
                "price": "6495.00",
                "is_active": True,
                "is_special_edition": False,
                "product": "550e8400-e29b-41d4-a716-446655440000",
                "optionIds": [
                    "550e8400-e29b-41d4-a716-446655440012",  # Blue
                    "550e8400-e29b-41d4-a716-446655440022",  # 41
                ],
                "attributes": [
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440001",
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440012"],
                    },
                    {
                        "attributeId": "550e8400-e29b-41d4-a716-446655440002",
                        "attributeValues": ["550e8400-e29b-41d4-a716-446655440022"],
                    },
                ],
            },
        ],
    },
    request_only=True,
    media_type="application/json",
)

STEP2_PATCH_EXAMPLE = OpenApiExample(
    "Bulk update variant prices and flags",
    description=(
        "Example showing how to update multiple variants at once. "
        "Each variant is identified by SKU, and you can update price, name, "
        "is_active, and is_special_edition fields."
    ),
    value={
        "generatedVarients": [
            {
                "sku": "CELSI-GREY-40",
                "price": "4995.00",
                "is_active": True,
            },
            {
                "sku": "CELSI-BLUE-40",
                "price": "5495.00",
                "is_special_edition": True,
            },
            {
                "sku": "CELSI-GREY-41",
                "name": "Grey - Size 41 (Limited)",
                "is_active": False,
            },
        ]
    },
    request_only=True,
    media_type="application/json",
)


@extend_schema(tags=["Product 2/3 - Attributes, Values & Price"])
class ProductVariantValuesView(SuccessEnvelopeMixin, APIView):
    permission_classes = [IsAdminUser]
    use_status_envelope = True

    def get_success_message(self, request) -> str:
        if request.method == "PATCH":
            return "ProductVarientValues updated successfully"
        return "ProductVarientValue created successfully"

    @extend_schema(
        request=ProductVariantValuesSerializer,
        responses={201: ProductVariantValuesResponseSerializer},
        summary="Step 2: Add attributes, values & prices",
        description=(
            "Step 2 of the product flow: save variants for a product "
            "created in step 1. Resolves the attribute palette to product "
            "values, then upserts each generated variant by SKU (same SKU "
            "updates, new SKU creates). \n\n"
            "**How it works:**\n"
            "1. Define the attribute palette (e.g., Color + Size)\n"
            "2. Specify all value combinations (options) for each attribute\n"
            "3. Create variants for each combination with price and SKU\n"
            "4. The system creates ProductAttributeValue rows and links them to variants"
        ),
        examples=[STEP2_POST_EXAMPLE],
    )
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        input_serializer = ProductVariantValuesSerializer(
            data=request.data, context={"product_id": str(product.pk)}
        )
        input_serializer.is_valid(raise_exception=True)
        result = ProductVariantValuesService.save_variants(
            product=product, **input_serializer.validated_data
        )
        output = ProductVariantValuesResponseSerializer(result)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=ProductVariantValuesPatchSerializer,
        responses={200: ProductVariantValuesResponseSerializer},
        summary="Step 2: Bulk update prices & flags",
        description=(
            "Step 2 of the product flow: bulk-update the price, name and "
            "flags of the product's variants. Each row is keyed by SKU and "
            "only the sent fields change; options stay as-is. Unknown SKUs "
            "fail the whole request atomically — nothing is created here.\n\n"
            "**Updatable fields:**\n"
            "- `price`: Update variant price\n"
            "- `name`: Update variant display name\n"
            "- `is_active`: Enable/disable variant\n"
            "- `is_special_edition`: Mark as special edition"
        ),
        examples=[STEP2_PATCH_EXAMPLE],
    )
    def patch(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        input_serializer = ProductVariantValuesPatchSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        result = ProductVariantValuesService.bulk_update_variants(
            product=product, **input_serializer.validated_data
        )
        output = ProductVariantValuesResponseSerializer(result)
        return Response(output.data)
