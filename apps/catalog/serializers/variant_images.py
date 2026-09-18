"""Serializers for the tab-3 image endpoints.

``GET`` lists the values *used on* a product (grouped by attribute) with
their current images; ``POST`` sets/appends images on one selected value;
``DELETE`` removes a single gallery image. Image slots reuse the standard
machinery (multipart parts, ``{"file": ...}`` part references, base64
data URIs, ``{url}``/``{name}`` references), so JSON and multipart clients
both work. Featured image is single (replace or ``null`` to clear);
additional images are appended.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .fields import AdditionalImagesField, ImageObjectField
from .variant_values import (
    VariantValueAttributeObjectSerializer,
    VariantValueOptionObjectSerializer,
)


# -- upload request --------------------------------------------------------


class ProductVariantImagesUploadSerializer(serializers.Serializer):
    value = serializers.UUIDField(
        help_text="Product value id (attribute-value row) from the GET listing."
    )
    feature_image = ImageObjectField(
        prefix="feature_image", required=False, allow_null=True
    )
    additional_images = AdditionalImagesField(required=False)

    def validate(self, attrs):
        if "feature_image" not in attrs and "additional_images" not in attrs:
            raise serializers.ValidationError(
                "Send feature_image and/or additional_images."
            )
        return attrs


class ProductVariantImagesMultipartSerializer(ProductVariantImagesUploadSerializer):
    """Binary-file request shape for multipart uploads (OpenAPI docs)."""

    feature_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Binary feature-image file. Omit to keep, null to clear.",
    )
    additional_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        help_text="Repeat this file part; every file is appended to the gallery.",
    )


# -- response --------------------------------------------------------------


class VariantGalleryImageSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    url = serializers.SerializerMethodField()
    title = serializers.CharField(read_only=True)
    caption = serializers.CharField(read_only=True)
    alt = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_url(self, image):
        name = getattr(getattr(image, "image", None), "name", "") or ""
        if not name:
            return None
        try:
            url = image.image.url
        except ValueError:
            return None
        try:
            request = self.context.get("request")
        except AttributeError:
            request = None
        if url.startswith("/") and request is not None:
            url = request.build_absolute_uri(url)
        return url


class VariantImageValueSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    value = VariantValueOptionObjectSerializer(
        source="attribute_value", read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    feature_image = ImageObjectField(
        prefix="feature_image", include_public_id=False, read_only=True
    )
    additional_images = VariantGalleryImageSerializer(many=True, read_only=True)


class VariantImageAttributeGroupSerializer(serializers.Serializer):
    attribute = VariantValueAttributeObjectSerializer(read_only=True)
    values = VariantImageValueSerializer(many=True, read_only=True)


class ProductVariantImagesResponseSerializer(serializers.Serializer):
    attributes = VariantImageAttributeGroupSerializer(many=True, read_only=True)


class ProductVariantImageUploadResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    attribute = VariantValueAttributeObjectSerializer(read_only=True)
    value = VariantValueOptionObjectSerializer(
        source="attribute_value", read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    feature_image = ImageObjectField(
        prefix="feature_image", include_public_id=False, read_only=True
    )
    additional_images = VariantGalleryImageSerializer(many=True, read_only=True)


class ProductVariantImageDeleteResponseSerializer(serializers.Serializer):
    """Empty-object docs marker for gallery-image DELETE (real body is {})."""
