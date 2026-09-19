"""Tab-3 endpoints.

``GET``/``POST /api/v1/productvarientimages/{product_id}/`` lists the values
used on a product (grouped, with images) and uploads images onto one value;
``DELETE .../images/{image_id}/`` removes a single gallery image (featured
is cleared with ``{"feature_image": null}``). Mounted outside
``/api/v1/admin/`` at the exact frontend paths but staff-only like every
other write endpoint.
"""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample
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


# Step 3 examples
STEP3_UPLOAD_JSON_EXAMPLE = OpenApiExample(
    "Upload feature and gallery images (JSON with URLs)",
    description=(
        "Upload images using JSON with image URLs or data URIs. "
        "The feature_image replaces any existing featured image (use null to clear). "
        "Additional_images are appended to the gallery."
    ),
    value={
        "value": "550e8400-e29b-41d4-a716-446655440011",  # ProductAttributeValue UUID (Grey)
        "feature_image": {
            "url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "title": "Grey Slippers Front View",
            "alt": "Grey wool felt slippers from front",
        },
        "additional_images": [
            {
                "url": "https://res.cloudinary.com/demo/image/upload/sample2.jpg",
                "title": "Side View",
                "caption": "Comfortable side profile",
                "alt": "Grey slippers side view",
                "sort_order": 1,
            },
            {
                "url": "https://res.cloudinary.com/demo/image/upload/sample3.jpg",
                "title": "Detail Shot",
                "caption": "Wool texture detail",
                "alt": "Close-up of wool felt material",
                "sort_order": 2,
            },
        ],
    },
    request_only=True,
    media_type="application/json",
)

STEP3_UPLOAD_DATAURI_EXAMPLE = OpenApiExample(
    "Upload with base64 data URIs",
    description=(
        "Upload images using base64-encoded data URIs inline in JSON. "
        "Useful for uploading files from browser/mobile without separate HTTP requests."
    ),
    value={
        "value": "550e8400-e29b-41d4-a716-446655440012",  # ProductAttributeValue UUID (Blue)
        "feature_image": {
            "file": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
            "title": "Blue Slippers",
            "alt": "Blue wool felt slippers",
        },
        "additional_images": [
            {
                "file": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
                "title": "Blue Slippers Detail",
                "sort_order": 1,
            }
        ],
    },
    request_only=True,
    media_type="application/json",
)

STEP3_CLEAR_FEATURE_EXAMPLE = OpenApiExample(
    "Clear feature image",
    description="Set feature_image to null to remove the featured image while keeping gallery images.",
    value={
        "value": "550e8400-e29b-41d4-a716-446655440011",
        "feature_image": None,
    },
    request_only=True,
    media_type="application/json",
)


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
            "the step-3 upload.\n\n"
            "**Response structure:**\n"
            "- `attributes`: Array of attribute groups (e.g., Color, Size)\n"
            "- Each group contains `values` with their images\n"
            "- Each value shows: `id`, `feature_image`, `additional_images`\n"
            "- Use the value `id` in POST request to upload images"
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
            "product's attribute values (e.g., upload images for 'Grey' color).\n\n"
            "**Three upload methods:**\n\n"
            "1. **JSON with URLs**: Send `{\"url\": \"https://...\"}` for each image\n"
            "2. **JSON with data URIs**: Send `{\"file\": \"data:image/jpeg;base64,...\"}` \n"
            "3. **Multipart form-data**: Upload binary files directly\n\n"
            "**Image behavior:**\n"
            "- `feature_image`: Replaces existing featured image (use `null` to clear)\n"
            "- `additional_images`: Appended to gallery (existing images kept)\n"
            "- Each image can have: `title`, `caption`, `alt`, `sort_order`\n\n"
            "**Value ID**: Get value IDs from the GET endpoint (list images)"
        ),
        examples=[
            STEP3_UPLOAD_JSON_EXAMPLE,
            STEP3_UPLOAD_DATAURI_EXAMPLE,
            STEP3_CLEAR_FEATURE_EXAMPLE,
        ],
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
            "Step 3 of the product flow: remove one gallery image from a "
            "product's attribute value. This deletes a single image from "
            "the `additional_images` array.\n\n"
            "**Note:** To clear the featured image, use POST with "
            "`{\"feature_image\": null}` instead of DELETE."
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
