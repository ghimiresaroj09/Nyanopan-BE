"""Django admin configuration for the catalog."""

from django.contrib import admin

from .models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttributeImage,
    ProductAttributeValue,
    ProductModel,
    ProductVariant,
    ProductVariantOption,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "product_count", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "is_active")}),
        (
            "Image",
            {"fields": ("image", "image_title", "image_caption", "image_alt")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Products"


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 0
    autocomplete_fields = ["attribute", "attribute_value"]
    readonly_fields = ["created_at", "updated_at"]
    fields = [
        "attribute",
        "attribute_value",
        "is_active",
        "feature_image",
        "feature_image_title",
        "feature_image_caption",
        "feature_image_alt",
        "created_at",
        "updated_at",
    ]


class ProductAttributeImageInline(admin.TabularInline):
    model = ProductAttributeImage
    extra = 0
    fields = ["image", "title", "caption", "alt", "sort_order"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fields = ["sku", "name", "price", "is_special_edition", "is_active", "created_at", "updated_at"]
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "model", "gender", "is_featured", "is_active", "updated_at"]
    list_filter = ["gender", "is_featured", "is_active", "category", "model"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["category", "model", "user"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductAttributeValueInline, ProductVariantInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "user", "category", "model", "gender")}),
        ("Content", {"fields": ("description", "general_information", "materials_used", "key_features")}),
        ("Visibility", {"fields": ("is_featured", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ["name", "requires_image", "is_active", "updated_at"]
    list_filter = ["requires_image", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [AttributeValueInline]


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ["name", "attribute", "is_active", "updated_at"]
    list_filter = ["attribute", "is_active"]
    search_fields = ["name", "attribute__name"]
    autocomplete_fields = ["attribute"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ["product", "attribute", "attribute_value", "is_active", "updated_at"]
    list_filter = ["attribute", "is_active"]
    search_fields = ["product__name", "attribute__name", "attribute_value__name"]
    autocomplete_fields = ["product", "attribute", "attribute_value"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductAttributeImageInline]
    fieldsets = (
        (None, {"fields": ("product", "attribute", "attribute_value", "is_active")}),
        (
            "Feature image",
            {
                "fields": (
                    "feature_image",
                    "feature_image_title",
                    "feature_image_caption",
                    "feature_image_alt",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),)


class ProductVariantOptionInline(admin.TabularInline):
    model = ProductVariantOption
    extra = 0
    autocomplete_fields = ["product_attribute_value"]
    readonly_fields = ["created_at"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "name", "price", "is_special_edition", "is_active"]
    list_filter = ["is_special_edition", "is_active"]
    search_fields = ["sku", "name", "product__name"]
    autocomplete_fields = ["product"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductVariantOptionInline]


@admin.register(ProductVariantOption)
class ProductVariantOptionAdmin(admin.ModelAdmin):
    list_display = ["variant", "product_attribute_value", "created_at"]
    search_fields = ["variant__sku", "variant__product__name"]
    autocomplete_fields = ["variant", "product_attribute_value"]
    readonly_fields = ["created_at"]
