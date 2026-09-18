"""Public read-only serializers. Only active records are ever serialized."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.common.utilities import format_price

from ..models import Attribute, AttributeValue, Category, Product, ProductModel
from .fields import PublicImageObjectField

IMAGE_SCHEMA = {
    "type": "object",
    "nullable": True,
    "description": "Single image (public payloads omit the internal asset name).",
    "properties": {
        "url": {
            "type": "string",
            "format": "uri",
            "example": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-main.jpg",
        },
        "title": {"type": "string", "example": "Grey Celsi Slippers"},
        "caption": {"type": "string", "example": "Grey wool felt slippers"},
        "alt": {"type": "string", "example": "Grey slippers"},
    },
}

PRICE_RANGE_SCHEMA = {
    "type": "object",
    "nullable": True,
    "properties": {
        "min_price": {"type": "string", "example": "5995.00"},
        "max_price": {"type": "string", "example": "6495.00"},
    },
}

ATTRIBUTES_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "attribute": {"type": "string"},
            "values": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string"},
                        "feature_image": IMAGE_SCHEMA,
                        "additional_images": {
                            "type": "array",
                            "items": {**IMAGE_SCHEMA, "nullable": False},
                        },
                    },
                },
            },
        },
    },
}

VARIANTS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "sku": {"type": "string"},
            "price": {"type": "string", "example": "5995.00"},
            "is_special_edition": {"type": "boolean"},
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_attribute_value": {"type": "string", "format": "uuid"},
                        "attribute": {"type": "string"},
                        "value": {"type": "string"},
                    },
                },
            },
        },
    },
}


def _absolute_media_url(context, url: str) -> str:
    """Absolutize a relative (local fallback) media URL using the request."""
    request = (context or {}).get("request")
    if url.startswith("/") and request is not None:
        return request.build_absolute_uri(url)
    return url


class CategoryPublicSerializer(serializers.ModelSerializer):
    image = PublicImageObjectField(prefix="image", read_only=True)
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "product_count"]


class ProductModelPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ["id", "name", "slug", "description"]


class AttributeValuePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ["id", "name"]


class AttributePublicSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = ["id", "name", "requires_image", "values"]

    @extend_schema_field(AttributeValuePublicSerializer(many=True))
    def get_values(self, obj):
        values = getattr(obj, "active_values", None)
        if values is None:  # fallback when the prefetch is missing
            values = obj.values.filter(is_active=True).order_by("name")
        return AttributeValuePublicSerializer(values, many=True).data


class CategoryNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductModelNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ["id", "name", "slug"]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight list card: no descriptions, no nested variants."""

    category = CategoryNestedSerializer(read_only=True)
    model = ProductModelNestedSerializer(read_only=True)
    price_range = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "gender",
            "category",
            "model",
            "is_featured",
            "price_range",
            "primary_image",
            "created_at",
        ]

    def _prefetched_variants(self, obj):
        variants = getattr(obj, "prefetched_variants", None)
        if variants is None:
            variants = list(
                obj.variants.filter(is_active=True)
                .order_by("price", "id")
            )
        return list(variants)

    @extend_schema_field(PRICE_RANGE_SCHEMA)
    def get_price_range(self, obj):
        variants = self._prefetched_variants(obj)
        if not variants:
            return None
        cheapest = variants[0]
        dearest = variants[-1]
        return {
            "min_price": format_price(cheapest.price),
            "max_price": format_price(dearest.price),
        }

    @extend_schema_field(IMAGE_SCHEMA)
    def get_primary_image(self, obj):
        images = getattr(obj, "prefetched_images", None)
        if images is None:
            pav = (
                obj.attribute_values.filter(
                    is_active=True,
                    attribute__is_active=True,
                    attribute_value__is_active=True,
                )
                .exclude(feature_image="")
                .order_by("-attribute__requires_image", "id")
                .first()
            )
        else:
            pav = images[0] if images else None
        if not pav or not pav.feature_image.name:
            return None
        return {
            "url": _absolute_media_url(self.context, pav.feature_image.url),
            "title": pav.feature_image_title or "",
            "caption": pav.feature_image_caption or "",
            "alt": pav.feature_image_alt or "",
        }


class ProductDetailSerializer(serializers.ModelSerializer):
    """Complete product page payload: attributes, images, and variants."""

    category = CategoryNestedSerializer(read_only=True)
    model = ProductModelNestedSerializer(read_only=True)
    attributes = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "gender",
            "description",
            "general_information",
            "materials_used",
            "category",
            "model",
            "key_features",
            "attributes",
            "variants",
        ]

    def _prefetched_pavs(self, obj):
        pavs = getattr(obj, "prefetched_pavs", None)
        if pavs is None:
            pavs = list(
                obj.attribute_values.filter(
                    is_active=True,
                    attribute__is_active=True,
                    attribute_value__is_active=True,
                )
                .select_related("attribute", "attribute_value")
                .order_by("id")
            )
        return list(pavs)

    def _prefetched_variants(self, obj):
        variants = getattr(obj, "prefetched_variants", None)
        if variants is None:
            variants = list(
                obj.variants.filter(is_active=True)
                .prefetch_related("options__product_attribute_value__attribute")
                .prefetch_related("options__product_attribute_value__attribute_value")
                .order_by("id")
            )
        return list(variants)

    @extend_schema_field(ATTRIBUTES_SCHEMA)
    def get_attributes(self, obj):
        groups: dict[int, dict] = {}
        for pav in self._prefetched_pavs(obj):
            group = groups.setdefault(
                pav.attribute_id,
                {"id": pav.attribute_id, "attribute": pav.attribute.name, "values": []},
            )
            feature_image = None
            if pav.feature_image.name:
                feature_image = {
                    "url": _absolute_media_url(self.context, pav.feature_image.url),
                    "title": pav.feature_image_title or "",
                    "caption": pav.feature_image_caption or "",
                    "alt": pav.feature_image_alt or "",
                }
            group["values"].append(
                {
                    "id": pav.id,
                    "name": pav.attribute_value.name,
                    "feature_image": feature_image,
                    "additional_images": [
                        {
                            "url": _absolute_media_url(self.context, image.image.url),
                            "title": image.title or "",
                            "caption": image.caption or "",
                            "alt": image.alt or "",
                        }
                        for image in pav.additional_images.all()
                        if image.image.name
                    ],
                }
            )
        return list(groups.values())

    @extend_schema_field(VARIANTS_SCHEMA)
    def get_variants(self, obj):
        payload = []
        for variant in self._prefetched_variants(obj):
            payload.append(
                {
                    "id": variant.id,
                    "sku": variant.sku,
                    "price": format_price(variant.price),
                    "is_special_edition": variant.is_special_edition,
                    "options": [
                        {
                            "product_attribute_value": option.product_attribute_value_id,
                            "attribute": option.product_attribute_value.attribute.name,
                            "value": option.product_attribute_value.attribute_value.name,
                        }
                        for option in variant.options.all()
                    ],
                }
            )
        return payload
