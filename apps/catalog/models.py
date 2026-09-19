"""Catalog models.

Relationship overview::

    Category ──< Product >── ProductModel
                    │
                    ├── key_features (JSON)
                    │
                    ├────< ProductAttributeValue >── Attribute
                    │         │                      AttributeValue
                    │         ├── feature_image (+ metadata, ImageField on shared storage)
                    │         └── additional_images >── ProductAttributeImage (ImageField rows)
                    │
                    └────< ProductVariant>
                                │
                                └────< ProductVariantOption
                                            └── ProductAttributeValue

Images live on the shared Cloudinary/filesystem storage via ImageFields; the database keeps asset names (.url builds delivery URLs) plus metadata.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import SluggedModelMixin, TimeStampedModel
from apps.common.storages import image_storage
from apps.common.validators import validate_image_upload, validate_key_features


def _image_path(folder, filename):
    base = (getattr(settings, "CLOUDINARY_UPLOAD_FOLDER", "") or "ecommerce").strip("/")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return f"{base}/{folder}/{name}"


def category_image_path(instance, filename):
    return _image_path("categories", filename)


def pav_feature_image_path(instance, filename):
    return _image_path("values", filename)


def pav_additional_image_path(instance, filename):
    return _image_path("values-additional", filename)


def product_feature_image_path(instance, filename):
    """Upload path: ecommerce/products/<uuid>.<ext>."""
    return _image_path("products", filename)


class Gender(models.TextChoices):
    MEN = "MEN", "Men"
    WOMEN = "WOMEN", "Women"
    UNISEX = "UNISEX", "Unisex"
    KIDS = "KIDS", "Kids"
    BABY = "BABY", "Baby"


class ImageMetadataMixin(models.Model):
    """Cloudinary image + presentation metadata for a single image field.

    ``image`` is an ``ImageField`` on the shared storage: the database keeps
    the asset name and ``image.url`` builds the delivery URL. Title/caption/
    alt ride alongside in plain columns.
    """

    image = models.ImageField(
        upload_to=category_image_path,
        storage=image_storage,
        validators=[validate_image_upload],
        blank=True,
    )
    image_title = models.CharField(max_length=255, blank=True, default="")
    image_caption = models.CharField(max_length=255, blank=True, default="")
    image_alt = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        abstract = True

    @property
    def has_image(self) -> bool:
        return bool(self.image.name)


class Category(TimeStampedModel, ImageMetadataMixin, SluggedModelMixin):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name


class ProductModel(TimeStampedModel, SluggedModelMixin):
    """A named product line/model, e.g. 'Celsi Wool Felt Slippers'."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self) -> str:
        return self.name


class Product(TimeStampedModel, SluggedModelMixin):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        help_text="Admin who created the product.",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    model = models.ForeignKey(ProductModel, on_delete=models.PROTECT, related_name="products")
    gender = models.CharField(max_length=10, choices=Gender.choices, db_index=True)
    description = models.TextField(blank=True, default="")
    general_information = models.TextField(blank=True, default="")
    materials_used = models.TextField(blank=True, default="")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    key_features = models.JSONField(default=list, blank=True)
    
    # Featured image for the product (main product image)
    feature_image = models.ImageField(
        upload_to=product_feature_image_path,
        storage=image_storage,
        validators=[validate_image_upload],
        blank=True,
        help_text="Main product image shown in listings and detail views.",
    )
    feature_image_title = models.CharField(max_length=255, blank=True, default="")
    feature_image_caption = models.CharField(max_length=255, blank=True, default="")
    feature_image_alt = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["gender", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()
        validate_key_features(self.key_features)
    
    @property
    def has_feature_image(self) -> bool:
        return bool(self.feature_image.name)


class Attribute(TimeStampedModel):
    """An extensible product attribute (Color, Size, Material, ...).

    ``requires_image`` declares whether every *active* product value of this
    attribute must carry a feature image (e.g. Color). New image-requiring
    attributes can be added without code changes.
    """

    name = models.CharField(max_length=100, unique=True)
    requires_image = models.BooleanField(
        default=False,
        help_text="When enabled, active product values of this attribute require a feature image.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AttributeValue(TimeStampedModel):
    """A global reusable value of an attribute (e.g. Color -> Grey)."""

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["attribute__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "name"], name="uniq_attribute_value"
            )
        ]
        indexes = [models.Index(fields=["attribute", "is_active"])]

    def __str__(self) -> str:
        return f"{self.attribute.name} → {self.name}"


class ProductAttributeValue(TimeStampedModel):
    """Product-specific use of an attribute value, with its own images.

    The same global ``AttributeValue`` (e.g. Color → Grey) may be used by many
    products; each usage is a separate row carrying that product's images.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="attribute_values"
    )
    attribute = models.ForeignKey(
        Attribute, on_delete=models.PROTECT, related_name="product_values"
    )
    attribute_value = models.ForeignKey(
        AttributeValue, on_delete=models.PROTECT, related_name="product_values"
    )

    feature_image = models.ImageField(
        upload_to=pav_feature_image_path,
        storage=image_storage,
        validators=[validate_image_upload],
        blank=True,
    )
    feature_image_title = models.CharField(max_length=255, blank=True, default="")
    feature_image_caption = models.CharField(max_length=255, blank=True, default="")
    feature_image_alt = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute", "attribute_value"],
                name="uniq_product_attribute_value",
            )
        ]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["attribute", "attribute_value"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name}: {self.attribute.name} → {self.attribute_value.name}"

    def clean(self):
        super().clean()
        if self.attribute_id and self.attribute_value_id:
            actual_attribute_id = (
                AttributeValue.objects.filter(pk=self.attribute_value_id)
                .values_list("attribute_id", flat=True)
                .first()
            )
            if actual_attribute_id is None:
                raise ValidationError(
                    {"attribute_value": "Selected attribute value does not exist."}
                )
            if actual_attribute_id != self.attribute_id:
                raise ValidationError(
                    {
                        "attribute_value": "Selected value does not belong to the selected attribute."
                    }
                )
        if self.attribute_id and self.is_active:
            attribute = (
                Attribute.objects.filter(pk=self.attribute_id)
                .values("name", "requires_image")
                .first()
            )
            if attribute and attribute["requires_image"] and not (self.feature_image.name or ""):
                raise ValidationError(
                    {
                        "feature_image": (
                            f"A feature image is required for '{attribute['name']}' values."
                        )
                    }
                )

    @property
    def has_feature_image(self) -> bool:
        return bool(self.feature_image.name)


class ProductAttributeImage(TimeStampedModel):
    """One additional image of a product attribute value (ordered gallery)."""

    product_attribute_value = models.ForeignKey(
        ProductAttributeValue, on_delete=models.CASCADE, related_name="additional_images"
    )
    image = models.ImageField(
        upload_to=pav_additional_image_path,
        storage=image_storage,
        validators=[validate_image_upload],
    )
    title = models.CharField(max_length=255, blank=True, default="")
    caption = models.CharField(max_length=255, blank=True, default="")
    alt = models.CharField(max_length=255, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at", "id"]

    def __str__(self) -> str:
        return f"Image #{self.sort_order} for {self.product_attribute_value_id}"


class ProductVariant(TimeStampedModel):
    """A purchasable combination of a product's attribute values."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="Leave blank to auto-generate from the product and options.",
    )
    name = models.CharField(max_length=200, blank=True, default="")
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    is_special_edition = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} ({self.product.name})"

    def save(self, *args, **kwargs):
        if not (self.sku or "").strip():
            from apps.catalog.services.sku import generate_fallback_sku

            self.sku = generate_fallback_sku()
        super().save(*args, **kwargs)

    def option_value_ids(self) -> frozenset[int]:
        return frozenset(
            self.options.values_list("product_attribute_value_id", flat=True)
        )


class ProductVariantOption(models.Model):
    """Through model linking a variant to one of its product's values.

    Invariants (enforced here, in serializers, and in the service layer):
    - the option's product must equal the variant's product;
    - a variant may hold at most one value per attribute.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="options"
    )
    product_attribute_value = models.ForeignKey(
        ProductAttributeValue, on_delete=models.PROTECT, related_name="variant_options"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "product_attribute_value"],
                name="uniq_variant_option",
            )
        ]
        indexes = [models.Index(fields=["variant", "product_attribute_value"])]

    def __str__(self) -> str:
        return f"{self.variant.sku} ← {self.product_attribute_value}"

    def clean(self):
        super().clean()
        pav = None
        if self.product_attribute_value_id:
            pav = (
                ProductAttributeValue.objects.select_related("attribute")
                .filter(pk=self.product_attribute_value_id)
                .first()
            )
            if pav is None:
                raise ValidationError(
                    {"product_attribute_value": "Invalid product attribute value."}
                )
        variant_product_id = None
        if self.variant_id:
            variant_product_id = (
                ProductVariant.objects.filter(pk=self.variant_id)
                .values_list("product_id", flat=True)
                .first()
            )
            if variant_product_id is None:
                raise ValidationError({"variant": "Invalid variant."})
        if (
            pav is not None
            and variant_product_id is not None
            and pav.product_id != variant_product_id
        ):
            raise ValidationError(
                {
                    "product_attribute_value": (
                        "Option must belong to the same product as the variant."
                    )
                }
            )
        if pav is not None and self.variant_id:
            clash = ProductVariantOption.objects.filter(
                variant_id=self.variant_id,
                product_attribute_value__attribute_id=pav.attribute_id,
            )
            if self.pk:
                clash = clash.exclude(pk=self.pk)
            if clash.exists():
                raise ValidationError(
                    {
                        "product_attribute_value": (
                            f"Variant already has a '{pav.attribute.name}' option."
                        )
                    }
                )
