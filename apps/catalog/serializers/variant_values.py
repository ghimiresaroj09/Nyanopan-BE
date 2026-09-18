"""Serializers for POST/PATCH /api/v1/productvarientvalues/{product_id}/.

Tab-2 contract: the frontend sends an attribute palette plus the variant
combinations it generated, and gets back the resolved palette plus the
created/updated variants. Key names (including ``generatedVarients``) match
the frontend contract exactly.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.common.utilities import format_zulu


# -- request ---------------------------------------------------------------


class VariantPaletteEntrySerializer(serializers.Serializer):
    attribute = serializers.UUIDField()
    options = serializers.ListField(
        child=serializers.UUIDField(), min_length=1
    )


class GeneratedVariantAttributeSerializer(serializers.Serializer):
    attributeId = serializers.UUIDField()
    attributeValues = serializers.ListField(
        child=serializers.UUIDField(), min_length=1
    )


class GeneratedVariantSerializer(serializers.Serializer):
    sku = serializers.CharField(
        max_length=100, required=False, default="", allow_blank=True
    )
    name = serializers.CharField(
        max_length=200, required=False, default="", allow_blank=True
    )
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    is_active = serializers.BooleanField(required=False, default=True)
    is_special_edition = serializers.BooleanField(required=False, default=False)
    optionIds = serializers.ListField(
        child=serializers.UUIDField(), min_length=1
    )
    attributes = GeneratedVariantAttributeSerializer(many=True, allow_empty=False)
    product = serializers.UUIDField()

    def validate(self, attrs):
        option_ids = {str(value) for value in attrs["optionIds"]}
        grouped = {
            str(value)
            for block in attrs["attributes"]
            for value in block["attributeValues"]
        }
        if option_ids != grouped:
            raise serializers.ValidationError(
                {"optionIds": "optionIds must match the attributeValues in attributes."}
            )
        product_id = self.context.get("product_id")
        if product_id is not None and str(attrs["product"]) != str(product_id):
            raise serializers.ValidationError(
                {"product": "Product must match the product in the URL."}
            )
        return attrs


class ProductVariantValuesSerializer(serializers.Serializer):
    attributes = VariantPaletteEntrySerializer(many=True, allow_empty=False)
    generatedVarients = GeneratedVariantSerializer(many=True, allow_empty=False)


class GeneratedVariantPatchSerializer(serializers.Serializer):
    """One bulk-update row: SKU selects the variant, sent fields change."""

    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )
    is_active = serializers.BooleanField(required=False)
    is_special_edition = serializers.BooleanField(required=False)

    def validate(self, attrs):
        updatable = ("name", "price", "is_active", "is_special_edition")
        if not any(field in attrs for field in updatable):
            raise serializers.ValidationError(
                "Provide at least one field to update: "
                "name, price, is_active, is_special_edition."
            )
        return attrs


class ProductVariantValuesPatchSerializer(serializers.Serializer):
    generatedVarients = GeneratedVariantPatchSerializer(many=True, allow_empty=False)


# -- response --------------------------------------------------------------


class VariantValueAttributeObjectSerializer(serializers.Serializer):
    object = serializers.SerializerMethodField()
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    isActive = serializers.BooleanField(source="is_active", read_only=True)
    created_date = serializers.SerializerMethodField()
    updated_date = serializers.SerializerMethodField()

    @extend_schema_field({"type": "string", "example": "attribute"})
    def get_object(self, obj):
        return "attribute"

    @extend_schema_field(
        {
            "type": "string",
            "format": "date-time",
            "example": "2026-09-17T10:00:00.000Z",
        }
    )
    def get_created_date(self, obj):
        return format_zulu(obj.created_at)

    @extend_schema_field(
        {
            "type": "string",
            "format": "date-time",
            "example": "2026-09-17T10:00:00.000Z",
        }
    )
    def get_updated_date(self, obj):
        return format_zulu(obj.updated_at)


class VariantValueOptionObjectSerializer(serializers.Serializer):
    object = serializers.SerializerMethodField()
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)

    @extend_schema_field({"type": "string", "example": "attributevalueitem"})
    def get_object(self, obj):
        return "attributevalueitem"


class VariantPaletteEchoSerializer(serializers.Serializer):
    attribute = VariantValueAttributeObjectSerializer(read_only=True)
    options = VariantValueOptionObjectSerializer(many=True, read_only=True)


class ProductVariantValueResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    product = serializers.UUIDField(source="product_id", read_only=True)
    sku = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, coerce_to_string=False, read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    is_special_edition = serializers.BooleanField(read_only=True)
    attributeGroups = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()

    @extend_schema_field({"type": "array", "items": {}, "example": []})
    def get_attributeGroups(self, variant):
        return []

    @extend_schema_field(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "attributeId": {"type": "string", "format": "uuid"},
                    "attributeValues": {
                        "type": "array",
                        "items": {"type": "string", "format": "uuid"},
                    },
                },
            },
        }
    )
    def get_attributes(self, variant):
        groups: list[dict] = []
        seen: dict[str, list] = {}
        options = variant.options.select_related(
            "product_attribute_value"
        ).order_by("created_at", "id")
        for option in options:
            pav = option.product_attribute_value
            key = str(pav.attribute_id)
            if key not in seen:
                seen[key] = []
                groups.append({"attributeId": key, "attributeValues": seen[key]})
            seen[key].append(str(pav.attribute_value_id))
        return groups


class ProductVariantValuesResponseSerializer(serializers.Serializer):
    attributes = VariantPaletteEchoSerializer(many=True, read_only=True)
    generatedVarients = ProductVariantValueResponseSerializer(many=True, read_only=True)
