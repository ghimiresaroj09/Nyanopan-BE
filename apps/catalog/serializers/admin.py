"""Admin read/write serializers. Writes delegate to the service layer."""

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.services.attributes import AttributeService
from apps.catalog.services.categories import CategoryService
from apps.catalog.services.products import (
    ProductAttributeValueService,
    ProductService,
)
from apps.catalog.services.variants import VariantService
from apps.common.validators import validate_image_upload

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
from .fields import (
    VALUE_NAME_MARKER,
    AdditionalImagesField,
    AttributeValueNameField,
    FlexibleRelatedField,
    ImageObjectField,
    KeyFeaturesField,
    OptionReferenceField,
)
from .public import CategoryNestedSerializer, ProductModelNestedSerializer

MISSING = object()


def _resolve_value_name(attribute, name):
    """Resolve a value ``name`` within ``attribute`` (or raise a guided error)."""
    if attribute is None:
        raise serializers.ValidationError(
            {"attribute_value": "Pass 'attribute' together with a value name (or use the value UUID)."}
        )
    match = AttributeValue.objects.filter(attribute=attribute, name=name).first()
    if match is None:
        near = list(AttributeValue.objects.filter(attribute=attribute, name__iexact=name)[:2])
        match = near[0] if len(near) == 1 else None
    if match is None:
        available = list(
            AttributeValue.objects.filter(attribute=attribute)
            .order_by("name")
            .values_list("name", flat=True)[:50]
        )
        hint = f" Available for '{attribute.name}': {', '.join(available)}." if available else ""
        raise serializers.ValidationError(
            {"attribute_value": f"No value '{name}' for attribute '{attribute.name}'.{hint}"}
        )
    return match


def _resolve_value_marker(attribute, raw):
    """Turn an ``AttributeValueNameField`` marker into an instance (pass-through otherwise)."""
    if isinstance(raw, dict) and VALUE_NAME_MARKER in raw:
        return _resolve_value_name(attribute, raw[VALUE_NAME_MARKER])
    return raw


class CategoryAdminSerializer(serializers.ModelSerializer):
    image = ImageObjectField(prefix="image", required=False, allow_null=True)
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "image",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"slug": {"required": False}}

    def create(self, validated_data):
        image = validated_data.pop("image", MISSING)
        kwargs = dict(validated_data)
        if image is not MISSING:
            kwargs["image"] = image
        return CategoryService.create_category(**kwargs)

    def update(self, instance, validated_data):
        return CategoryService.update_category(category=instance, data=validated_data)


class ProductModelAdminSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = ProductModel
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"slug": {"required": False}}


class AttributeAdminSerializer(serializers.ModelSerializer):
    values_count = serializers.IntegerField(read_only=True, default=0)
    value = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        write_only=True,
        max_length=200,
        help_text=(
            "Value names to create with the attribute (all-or-nothing on create), "
            "or ensure exist on update (existing names are left untouched)."
        ),
    )
    values = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attribute
        fields = ["id", "name", "requires_image", "is_active", "values_count", "value", "values", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    @extend_schema_field({"type": "array", "items": {"type": "string"}})
    def get_values(self, obj):
        return [row.name for row in obj.values.all()]

    def create(self, validated_data):
        value_names = validated_data.pop("value", None)
        return AttributeService.create_attribute(data=validated_data, value_names=value_names)

    def update(self, instance, validated_data):
        value_names = validated_data.pop("value", None)
        return AttributeService.update_attribute(
            attribute=instance, data=validated_data, value_names=value_names
        )


class AttributeValueAdminSerializer(serializers.ModelSerializer):
    attribute = FlexibleRelatedField(
        queryset=Attribute.objects.all(),
        lookup_field="name",
        lookup_label="name",
        help_text="Attribute UUID or name.",
    )
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = AttributeValue
        fields = [
            "id",
            "attribute",
            "attribute_name",
            "name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProductAttributeValueAdminSerializer(serializers.ModelSerializer):
    product = FlexibleRelatedField(
        queryset=Product.objects.all(),
        lookup_field="slug",
        lookup_label="slug",
        help_text="Product UUID or slug.",
    )
    attribute = FlexibleRelatedField(
        queryset=Attribute.objects.all(),
        lookup_field="name",
        lookup_label="name",
        help_text="Attribute UUID or name.",
    )
    attribute_value = AttributeValueNameField(
        queryset=AttributeValue.objects.all(),
        help_text="Value UUID, or a name resolved within the attribute.",
    )
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)
    value_name = serializers.CharField(source="attribute_value.name", read_only=True)
    feature_image = ImageObjectField(
        prefix="feature_image", required=False, allow_null=True
    )
    additional_images = AdditionalImagesField(required=False)

    class Meta:
        model = ProductAttributeValue
        fields = [
            "id",
            "product",
            "attribute",
            "attribute_name",
            "attribute_value",
            "value_name",
            "feature_image",
            "additional_images",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def to_internal_value(self, data):
        attrs = super().to_internal_value(data)
        # Resolve value-name markers before DRF's auto uniqueness validators
        # run (they filter the queryset with these values).
        raw = attrs.get("attribute_value")
        if isinstance(raw, dict) and VALUE_NAME_MARKER in raw:
            attribute = attrs.get("attribute", getattr(self.instance, "attribute", None))
            attrs["attribute_value"] = _resolve_value_name(attribute, raw[VALUE_NAME_MARKER])
        return attrs

    def validate(self, attrs):
        instance = self.instance
        attribute = attrs.get("attribute", getattr(instance, "attribute", None))
        attribute_value = attrs.get("attribute_value", getattr(instance, "attribute_value", None))
        if attribute is not None and attribute_value is not None:
            if attribute_value.attribute_id != attribute.id:
                raise serializers.ValidationError(
                    {"attribute_value": "Selected value does not belong to the selected attribute."}
                )
        feature_image = attrs.get("feature_image", MISSING)
        if feature_image is MISSING and instance is not None:
            current_name = instance.feature_image.name or ""
            feature_image = None if not current_name else {"name": current_name}
        is_active = attrs.get("is_active", getattr(instance, "is_active", True))
        if attribute is not None and is_active and attribute.requires_image:
            if feature_image is MISSING or not feature_image:
                has_image = False
            else:
                # A new upload, or a reference to an existing asset.
                has_image = "file" in feature_image or bool(feature_image.get("name"))
            if not has_image:
                raise serializers.ValidationError(
                    {"feature_image": f"A feature image is required for '{attribute.name}' values."}
                )
        return attrs

    def create(self, validated_data):
        product = validated_data.pop("product")
        return ProductAttributeValueService.create_pav(product=product, data=validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("product", None)  # PAVs are never moved between products
        return ProductAttributeValueService.update_pav(pav=instance, data=validated_data)


class VariantOptionDetailSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(
        source="product_attribute_value.attribute.name", read_only=True
    )
    value = serializers.CharField(
        source="product_attribute_value.attribute_value.name", read_only=True
    )

    class Meta:
        model = ProductVariantOption
        fields = ["id", "product_attribute_value", "attribute", "value"]


class VariantAdminSerializer(serializers.ModelSerializer):
    product = FlexibleRelatedField(
        queryset=Product.objects.all(),
        lookup_field="slug",
        lookup_label="slug",
        help_text="Product UUID or slug.",
    )
    product_name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    options = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="ProductAttributeValue ids composing this variant (required on create).",
    )
    options_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "name",
            "price",
            "is_special_edition",
            "is_active",
            "options",
            "options_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"sku": {"help_text": "Leave blank to auto-generate from product + options."}}

    @extend_schema_field(VariantOptionDetailSerializer(many=True))
    def get_options_detail(self, obj):
        options = obj.options.all()
        return VariantOptionDetailSerializer(options, many=True).data

    def validate(self, attrs):
        instance = self.instance
        product = attrs.get("product", getattr(instance, "product", None))
        if product is None:
            raise serializers.ValidationError({"product": "This field is required."})
        if "options" in attrs:
            VariantService.validate_option_set(
                product=product,
                pav_ids=list(attrs["options"]),
                exclude_variant_id=instance.pk if instance else None,
            )
        elif instance is None:
            raise serializers.ValidationError({"options": "This field is required."})
        return attrs

    def create(self, validated_data):
        options = validated_data.pop("options")
        return VariantService.create_variant(option_pav_ids=options, **validated_data)

    def update(self, instance, validated_data):
        options = validated_data.pop("options", None)
        validated_data.pop("product", None)  # variants are never moved between products
        return VariantService.update_variant(
            variant=instance, option_pav_ids=options, **validated_data
        )


class VariantOptionAdminSerializer(serializers.ModelSerializer):
    variant = FlexibleRelatedField(
        queryset=ProductVariant.objects.all(),
        lookup_field="sku",
        lookup_label="SKU",
        help_text="Variant UUID or SKU.",
    )
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta:
        model = ProductVariantOption
        fields = ["id", "variant", "variant_sku", "product_attribute_value", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        instance = self.instance
        variant = attrs.get("variant", getattr(instance, "variant", None))
        pav = attrs.get("product_attribute_value", getattr(instance, "product_attribute_value", None))
        if variant is None:
            raise serializers.ValidationError({"variant": "This field is required."})
        if pav is None:
            raise serializers.ValidationError({"product_attribute_value": "This field is required."})
        current_ids = list(
            variant.options.exclude(pk=instance.pk if instance else None).values_list(
                "product_attribute_value_id", flat=True
            )
        )
        VariantService.validate_option_set(
            product=variant.product,
            pav_ids=[*current_ids, pav.pk],
            exclude_variant_id=variant.pk,
        )
        return attrs

    def create(self, validated_data):
        return VariantService.add_option(
            variant=validated_data["variant"],
            pav_id=validated_data["product_attribute_value"].pk,
        )

    def update(self, instance, validated_data):
        validated_data.pop("variant", None)
        new_pav = validated_data.get("product_attribute_value")
        if new_pav is None or new_pav.pk == instance.product_attribute_value_id:
            return instance
        return VariantService.change_option(option=instance, new_pav_id=new_pav.pk)


# ---------------------------------------------------------------------------
# Nested product write serializers
# ---------------------------------------------------------------------------
class ProductAttributeValueNestedSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    key = serializers.CharField(required=False, allow_blank=False, max_length=50)
    attribute = FlexibleRelatedField(
        queryset=Attribute.objects.all(),
        lookup_field="name",
        lookup_label="name",
        required=False,
        help_text="Attribute UUID or name.",
    )
    attribute_value = AttributeValueNameField(
        queryset=AttributeValue.objects.all(),
        required=False,
        help_text="Value UUID, or a name resolved within the attribute.",
    )
    feature_image = ImageObjectField(
        prefix="feature_image", required=False, allow_null=True
    )
    additional_images = AdditionalImagesField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        raw_value = attrs.get("attribute_value")
        if isinstance(raw_value, dict) and VALUE_NAME_MARKER in raw_value:
            attribute = attrs.get("attribute")
            if attribute is None and attrs.get("id") is not None:
                attribute = Attribute.objects.filter(product_values__id=attrs["id"]).first()
            attrs["attribute_value"] = _resolve_value_name(attribute, raw_value[VALUE_NAME_MARKER])
        if attrs.get("id") is None:
            missing = [
                field
                for field in ("attribute", "attribute_value")
                if field not in attrs
            ]
            if missing:
                raise serializers.ValidationError(
                    {field: "This field is required when creating a value." for field in missing}
                )
            attribute = attrs["attribute"]
            attribute_value = attrs["attribute_value"]
            if attribute_value.attribute_id != attribute.id:
                raise serializers.ValidationError(
                    {"attribute_value": "Selected value does not belong to the selected attribute."}
                )
            is_active = attrs.get("is_active", True)
            feature_image = attrs.get("feature_image", MISSING)
            if feature_image is MISSING or not feature_image:
                has_image = False
            else:
                # A new upload, or a reference to an existing asset.
                has_image = "file" in feature_image or bool(feature_image.get("name"))
            if attribute.requires_image and is_active and not has_image:
                # On create there is no pre-existing image, so require one now.
                raise serializers.ValidationError(
                    {"feature_image": f"A feature image is required for '{attribute.name}' values."}
                )
        return attrs


class VariantNestedSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    sku = serializers.CharField(
        required=False, max_length=100, help_text="Leave blank to auto-generate."
    )
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    name = serializers.CharField(required=False, max_length=200, allow_blank=True)
    is_special_edition = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    options = serializers.ListField(child=OptionReferenceField(), required=False)

    def validate(self, attrs):
        if attrs.get("id") is None:
            missing = [
                field
                for field in ("price", "options")
                if field not in attrs
            ]
            if missing:
                raise serializers.ValidationError(
                    {field: "This field is required when creating a variant." for field in missing}
                )
            if not attrs["options"]:
                raise serializers.ValidationError({"options": ["At least one option is required."]})
        return attrs


class ProductAdminWriteSerializer(serializers.ModelSerializer):
    model = FlexibleRelatedField(
        queryset=ProductModel.objects.all(),
        lookup_field="slug",
        lookup_label="slug",
        help_text="Product model UUID or slug.",
    )
    category = FlexibleRelatedField(
        queryset=Category.objects.all(),
        lookup_field="slug",
        lookup_label="slug",
        help_text="Category UUID or slug.",
    )
    key_features = KeyFeaturesField(required=False)
    attribute_values = ProductAttributeValueNestedSerializer(many=True, required=False)
    variants = VariantNestedSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "model",
            "gender",
            "description",
            "general_information",
            "materials_used",
            "category",
            "is_featured",
            "is_active",
            "key_features",
            "attribute_values",
            "variants",
        ]
        extra_kwargs = {
            "slug": {"required": False},
            "description": {"required": False},
            "general_information": {"required": False},
            "materials_used": {"required": False},
        }

    def validate(self, attrs):
        keys = [
            item["key"]
            for item in attrs.get("attribute_values", [])
            if item.get("key")
        ]
        if len(set(keys)) != len(keys):
            raise serializers.ValidationError(
                {"attribute_values": ["Temporary keys must be unique within the request."]}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return ProductService.create_product(user=user, data=validated_data)

    def update(self, instance, validated_data):
        return ProductService.update_product(product=instance, data=validated_data)


class ProductModelObjectSerializer(serializers.ModelSerializer):
    """Nested model object for product responses (note the camelCase flag)."""

    isActive = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = ProductModel
        fields = ["id", "name", "slug", "description", "isActive"]


class CategoryObjectSerializer(serializers.ModelSerializer):
    """Nested category object for product responses (note the camelCase flag)."""

    isActive = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "isActive"]


class ProductAdminResponseSerializer(serializers.ModelSerializer):
    """Lean product shape: scalars plus nested model/category objects.

    Values and variants live behind their own standalone endpoints and are
    intentionally absent here.
    """

    model = ProductModelObjectSerializer(read_only=True)
    category = CategoryObjectSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "model",
            "gender",
            "description",
            "general_information",
            "materials_used",
            "category",
            "is_featured",
            "key_features",
        ]


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    folder = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_folder(self, value):
        return value.strip()

    def validate_image(self, value):
        try:
            return validate_image_upload(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))


class ImageUploadResponseSerializer(serializers.Serializer):
    public_id = serializers.CharField()
    url = serializers.URLField()
    width = serializers.IntegerField(allow_null=True)
    height = serializers.IntegerField(allow_null=True)
    format = serializers.CharField(allow_blank=True)


class ImageDeleteSerializer(serializers.Serializer):
    public_id = serializers.CharField(max_length=255)


class ImageDeleteResponseSerializer(serializers.Serializer):
    """Result of deleting an uploaded asset."""

    deleted = serializers.BooleanField()


class CategoryMultipartSerializer(CategoryAdminSerializer):
    """Binary-file request shape for multipart category writes (OpenAPI docs)."""

    image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Binary image file. Omit to keep the current image, null to clear it.",
    )


class ProductAttributeValueMultipartSerializer(ProductAttributeValueAdminSerializer):
    """Binary-file request shape for multipart value writes (OpenAPI docs)."""

    feature_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Binary feature-image file. Omit to keep, null to clear.",
    )
    additional_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        help_text="Repeat this file part for multiple additional images.",
    )


class ProductMultipartSerializer(ProductAdminWriteSerializer):
    """Multipart request shape for product writes (OpenAPI docs).

    Scalar fields go in as flat parts; nested payloads go in as JSON-encoded
    strings, with image slots referencing file parts via {"file": "<part-name>"}.
    """

    attribute_values = serializers.CharField(
        required=False,
        help_text=(
            'JSON-encoded array of nested value objects (same shape as the '
            'application/json body). Example: [{"key": "grey", "attribute": '
            '"<uuid>", "attribute_value": "<uuid>", "feature_image": {"file": '
            '"grey-img"}}], plus a grey-img file part.'
        ),
    )
    variants = serializers.CharField(
        required=False,
        help_text="JSON-encoded array of nested variant objects.",
    )
    key_features = serializers.CharField(
        required=False,
        help_text="JSON-encoded [{title, value}, ...] array.",
    )


class AttributeValueBulkCreateSerializer(serializers.Serializer):
    """Bulk input: {"attribute": "<uuid or name>", "value": ["One", "Two", ...]}."""

    attribute = FlexibleRelatedField(
        queryset=Attribute.objects.all(),
        lookup_field="name",
        lookup_label="name",
        help_text="Attribute UUID or name.",
    )
    value = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=200,
    )
