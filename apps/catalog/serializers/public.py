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
        # Use product's feature_image if available
        if obj.feature_image and obj.feature_image.name:
            return {
                "url": _absolute_media_url(self.context, obj.feature_image.url),
                "title": obj.feature_image_title or "",
                "caption": obj.feature_image_caption or "",
                "alt": obj.feature_image_alt or "",
            }
        
        # Fallback to first attribute value feature image if product has no feature_image
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
    """Complete product page payload: attributes, images, and variants with nested structure."""

    category = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    feature_image = serializers.SerializerMethodField()
    product_images = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    product_varient_values = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    is_featured = serializers.BooleanField()
    usage_location = serializers.CharField()
    sole_type = serializers.CharField(required=False, allow_null=True)
    materials_used = serializers.CharField()
    general_information = serializers.CharField()
    key_features = serializers.JSONField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "model",
            "gender",
            "usage_location",
            "sole_type",
            "attributes",
            "category",
            "feature_image",
            "product_images",
            "materials_used",
            "general_information",
            "key_features",
            "is_active",
            "is_featured",
            "rating",
            "product_varient_values",
        ]

    def get_model(self, obj):
        return {
            "object": "productmodel",
            "id": str(obj.model.slug) if obj.model else None,
            "name": obj.model.name if obj.model else None,
        }

    def get_category(self, obj):
        return {
            "object": "category",
            "id": str(obj.category.slug) if obj.category else None,
            "name": obj.category.name if obj.category else None,
            "slug": obj.category.slug if obj.category else None,
        }

    def get_feature_image(self, obj):
        if not obj.feature_image.name:
            return None
        return {
            "url": _absolute_media_url(self.context, obj.feature_image.url),
            "title": obj.feature_image_title or "",
            "alt": obj.feature_image_alt or "",
        }

    def get_product_images(self, obj):
        # Placeholder for general product images (not attribute-specific)
        return []

    def get_rating(self, obj):
        return {
            "average": 0,
            "total": 0,
            "descriptions": [],
        }

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
                .prefetch_related("additional_images")
                .order_by("attribute__name", "attribute_value__name")
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
        """Group PAVs by attribute with full nested structure."""
        groups: dict[int, dict] = {}
        
        for pav in self._prefetched_pavs(obj):
            if pav.attribute_id not in groups:
                groups[pav.attribute_id] = {
                    "attribute": {
                        "object": "attribute",
                        "id": str(pav.attribute.id),
                        "name": pav.attribute.name,
                        "isActive": pav.attribute.is_active,
                    },
                    "attributeValues": [],
                }
            
            # Build feature image
            feature_image = None
            if pav.feature_image.name:
                feature_image = {
                    "url": _absolute_media_url(self.context, pav.feature_image.url),
                    "title": pav.feature_image_title or "",
                    "alt": pav.feature_image_alt or "",
                }
            
            # Build additional images
            additional_images = []
            for image in pav.additional_images.all():
                if image.image.name:
                    additional_images.append({
                        "url": _absolute_media_url(self.context, image.image.url),
                        "title": image.title or "",
                        "caption": image.caption or "",
                        "alt": image.alt or "",
                        "sortOrder": image.sort_order,
                    })
            
            # Build attribute value item
            value_item = {
                "object": "attributevalueitem",
                "id": str(pav.attribute_value.id),  # ← FIXED: Return AttributeValue.id, not ProductAttributeValue.id
                "name": pav.attribute_value.name,
            }
            
            if feature_image:
                value_item["featureImage"] = feature_image
            
            if additional_images:
                value_item["additionalImages"] = additional_images
            
            groups[pav.attribute_id]["attributeValues"].append(value_item)
        
        return list(groups.values())

    @extend_schema_field(VARIANTS_SCHEMA)
    def get_product_varient_values(self, obj):
        """Return variants with nested attribute structure."""
        payload = []
        
        for variant in self._prefetched_variants(obj):
            # Group options by attribute
            options_by_attribute = {}
            option_ids = []
            
            for option in variant.options.all():
                pav = option.product_attribute_value
                option_ids.append(str(pav.id))
                
                attr_id = pav.attribute_id
                if attr_id not in options_by_attribute:
                    options_by_attribute[attr_id] = {
                        "attribute": {
                            "object": "attribute",
                            "id": str(pav.attribute.id),
                            "name": pav.attribute.name,
                        },
                        "attributeValues": [],
                    }
                
                options_by_attribute[attr_id]["attributeValues"].append({
                    "object": "attributevalueitem",
                    "id": str(pav.attribute_value.id),  # ← FIXED: Return AttributeValue.id, not ProductAttributeValue.id
                    "name": pav.attribute_value.name,
                })
            
            payload.append({
                "id": str(variant.id),
                "name": variant.name or "",
                "sku": variant.sku,
                "price": float(variant.price),
                "isActive": variant.is_active,
                "isSpecialEdition": variant.is_special_edition,
                "optionIds": option_ids,
                "attributes": list(options_by_attribute.values()),
            })
        
        return payload
