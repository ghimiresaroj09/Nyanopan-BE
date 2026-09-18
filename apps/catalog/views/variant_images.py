"""Tab-3 endpoints.

``GET``/``POST /api/v1/productvarientimages/{product_id}/`` lists the values
used on a product (grouped, with images) and uploads images onto one value;
``DELETE .../images/{image_id}/`` removes a single gallery image (featured
is cleared with ``{"feature_image": null}``). Mounted outside
``/api/v1/admin/`` at the exact frontend paths but staff-only like every
other write endpoint.
"""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.responses import SuccessEnvelopeMixin

from ..models import Product, ProductAttributeImage
from ..serializers.variant_images import (
    ProductVariantImageDeleteResponseSerializer,
    ProductVariantImageUploadResponseSerializer,
    ProductVariantImagesMultipartSerializer,
    ProductVariantImagesResponseSerializer,
    ProductVariantImagesUploadSerializer,
)
from ..services.variant_images import ProductVariantImagesService
from .admin import _decode_multipart_data


@extend_schema(tags=["Product 3/3 - Images"])
class ProductVariantImagesView(SuccessEnvelopeMixin, APIView):
    permission_classes = [IsAdminUser]
    use_status_envelope = True

    def get_success_message(self, request) -> str:
        if request.method == "GET":
            return "ProductVarientImages retrieved successfully"
        return "ProductVarientImage uploaded successfully"

    @extend_schema(
        responses={200: ProductVariantImagesResponseSerializer},
        summary="List product images",
        description=(
            "Step 3 of the product flow: list the attribute values used on "
            "a product, grouped by attribute with their current featured "
            "and gallery images. Use the value ids from this listing in "
            "the step-3 upload."
        ),
    )
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        result = ProductVariantImagesService.listing(product=product)
        output = ProductVariantImagesResponseSerializer(
            result, context={"request": request}
        )
        return Response(output.data)

    @extend_schema(
        request={
            "application/json": ProductVariantImagesUploadSerializer,
            "multipart/form-data": ProductVariantImagesMultipartSerializer,
        },
        responses={201: ProductVariantImageUploadResponseSerializer},
        summary="Step 3: Upload images",
        description=(
            "Step 3 of the product flow: upload images onto one of the "
            "product's values. Send JSON "
            "with data-URI ``{\"file\": ...}`` / ``{\"url\": ...}`` slots, "
            "or multipart with a binary ``feature_image`` part and/or "
            "repeated ``additional_images`` parts. Featured image is "
            "replaced (``null`` clears it); gallery images are appended."
        ),
    )
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        data = request.data
        if (request.content_type or "").startswith("multipart/"):
            data = _decode_multipart_data(data, ("feature_image", "additional_images"))
        input_serializer = ProductVariantImagesUploadSerializer(
            data=data, context={"request": request}
        )
        input_serializer.is_valid(raise_exception=True)
        pav = ProductVariantImagesService.upload_images(
            product=product, data=input_serializer.validated_data
        )
        output = ProductVariantImageUploadResponseSerializer(
            pav, context={"request": request}
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Product 3/3 - Images"])
class ProductVariantImageDetailView(SuccessEnvelopeMixin, APIView):
    permission_classes = [IsAdminUser]
    use_status_envelope = True
    success_message = "ProductVarientImage deleted successfully"

    @extend_schema(
        responses={200: ProductVariantImageDeleteResponseSerializer},
        summary="Delete a gallery image",
        description=(
            "Step 3 of the product flow: remove one gallery image from the "
            "product's values."
        ),
    )
    def delete(self, request, product_id, image_id):
        image = get_object_or_404(
            ProductAttributeImage,
            pk=image_id,
            product_attribute_value__product_id=product_id,
        )
        ProductVariantImagesService.delete_gallery_image(image=image)
        return Response({}, status=status.HTTP_200_OK)
