"""Tab-2 endpoint: POST/PATCH /api/v1/productvarientvalues/{product_id}/.

Mounted outside ``/api/v1/admin/`` (exact frontend path) but staff-only like
every other write endpoint.
"""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
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
            "updates, new SKU creates)."
        ),
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
            "fail the whole request atomically — nothing is created here."
        ),
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
