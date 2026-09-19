"""Product + ProductAttributeValue mutations.

``ProductService.create_product`` / ``update_product`` support nested
attribute-value and variant payloads (with client temp ``key`` references so
variants can point at values created in the same request). Everything runs
inside a single transaction: any nested failure rolls the whole operation
back, leaving no partially-created products.
"""

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import to_drf_validation_error

from ..models import (
    Product,
    ProductAttributeImage,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantOption,
)
from .images import ImageService
from .variants import VariantService

_UNSET: object = object()

_PRODUCT_SCALAR_FIELDS = (
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
    # Note: feature_image is handled separately via ImageService
)


def _indexed_error(container: str, index: int, detail) -> ValidationError:
    if isinstance(detail, DjangoValidationError):
        detail = getattr(detail, "message_dict", {"non_field_errors": detail.messages})
    elif isinstance(detail, ValidationError):
        detail = detail.detail
    return ValidationError({container: {index: detail}})


class ProductAttributeValueService:
    """Standalone CRUD for product attribute values (also reused by ProductService)."""

    @staticmethod
    def _apply_fields(pav: ProductAttributeValue, data: dict, *, partial: bool) -> str:
        """Apply scalar + feature-image fields; returns the replaced feature name."""
        for field in ("attribute", "attribute_value", "is_active"):
            if field in data:
                setattr(pav, field, data[field])
        old_feature_name = ""
        if "feature_image" in data or not partial:
            marker = data.get("feature_image")
            old_feature_name = ImageService.set_image(pav, "feature_image", marker)
            ImageService.apply_metadata(pav, "feature_image", marker)
        return old_feature_name

    @staticmethod
    def _sync_additional_images(pav: ProductAttributeValue, markers: list | None) -> None:
        """Replace the PAV's additional-image rows; removed assets are cleaned up."""
        old_names = [image.image.name or "" for image in pav.additional_images.all()]
        pav.additional_images.all().delete()
        new_names = []
        for order, marker in enumerate(markers or []):
            row = ProductAttributeImage(product_attribute_value=pav, sort_order=order)
            ImageService.set_image(row, "image", marker)
            row.title = (marker or {}).get("title", "") or ""
            row.caption = (marker or {}).get("caption", "") or ""
            row.alt = (marker or {}).get("alt", "") or ""
            try:
                row.full_clean()
            except DjangoValidationError as exc:
                raise to_drf_validation_error(exc)
            row.save()
            new_names.append(row.image.name or "")
        ImageService.schedule_names_cleanup(
            [name for name in old_names if name and name not in new_names]
        )

    @staticmethod
    @transaction.atomic
    def create_pav(*, product: Product, data: dict) -> ProductAttributeValue:
        pav = ProductAttributeValue(product=product)
        ProductAttributeValueService._apply_fields(pav, data, partial=False)
        try:
            pav.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        pav.save()
        if "additional_images" in data:
            ProductAttributeValueService._sync_additional_images(pav, data["additional_images"])
        return pav

    @staticmethod
    @transaction.atomic
    def update_pav(*, pav: ProductAttributeValue, data: dict) -> ProductAttributeValue:
        old_feature_name = ProductAttributeValueService._apply_fields(pav, data, partial=True)
        try:
            pav.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        pav.save()
        if "feature_image" in data:
            ImageService.schedule_replaced_cleanup(old_feature_name, pav.feature_image.name or "")
        if "additional_images" in data:
            ProductAttributeValueService._sync_additional_images(pav, data["additional_images"])
        return pav

    @staticmethod
    @transaction.atomic
    def delete_pav(*, pav: ProductAttributeValue) -> None:
        names = [pav.feature_image.name or ""]
        names += [image.image.name or "" for image in pav.additional_images.all()]
        pav.delete()  # PROTECTed variant options raise before cleanup runs
        ImageService.schedule_names_cleanup(names)


class ProductService:
    # -- nested helpers ----------------------------------------------------------
    @staticmethod
    def _create_nested_pav(product: Product, item: dict, index: int) -> ProductAttributeValue:
        data = {
            "attribute": item["attribute"],
            "attribute_value": item["attribute_value"],
            "is_active": item.get("is_active", True),
            "additional_images": item.get("additional_images", []),
            "feature_image": item.get("feature_image", _UNSET),
        }
        if data["feature_image"] is _UNSET:
            data.pop("feature_image")
        try:
            return ProductAttributeValueService.create_pav(product=product, data=data)
        except ValidationError as exc:
            raise _indexed_error("attribute_values", index, exc)

    @staticmethod
    def _update_nested_pav(product: Product, item: dict, index: int, key_map: dict) -> ProductAttributeValue:
        pav = (
            ProductAttributeValue.objects.filter(pk=item["id"], product=product).first()
            if item.get("id") is not None
            else None
        )
        if item.get("id") is not None and pav is None:
            raise ValidationError(
                {
                    "attribute_values": {
                        index: {"id": ["This value does not belong to this product."]}
                    }
                }
            )
        if pav is None:
            pav = ProductService._create_nested_pav(product, item, index)
        else:
            data = {
                key: item[key]
                for key in ("attribute", "attribute_value", "is_active", "additional_images", "feature_image")
                if key in item
            }
            try:
                pav = ProductAttributeValueService.update_pav(pav=pav, data=data)
            except ValidationError as exc:
                raise _indexed_error("attribute_values", index, exc)
        if item.get("key"):
            key_map[item["key"]] = pav
        return pav

    @staticmethod
    def _resolve_option_refs(refs: list, key_map: dict, *, container: str, index: int) -> list[int]:
        pav_ids: list[int] = []
        for ref in refs or []:
            if isinstance(ref, dict) and "key" in ref:
                pav = key_map.get(ref["key"])
                if pav is None:
                    raise ValidationError(
                        {container: {index: {"options": [f"Unknown value reference '{ref['key']}'."]}}}
                    )
                pav_ids.append(pav.pk)
            elif isinstance(ref, dict) and "id" in ref:
                pav_ids.append(ref["id"])
            else:
                pav_ids.append(ref)
        return pav_ids

    @staticmethod
    def _create_nested_variant(product: Product, item: dict, index: int, key_map: dict) -> ProductVariant:
        pav_ids = ProductService._resolve_option_refs(
            item.get("options", []), key_map, container="variants", index=index
        )
        try:
            return VariantService.create_variant(
                product=product,
                sku=item.get("sku", ""),
                name=item.get("name", ""),
                price=item["price"],
                is_special_edition=item.get("is_special_edition", False),
                is_active=item.get("is_active", True),
                option_pav_ids=pav_ids,
            )
        except ValidationError as exc:
            raise _indexed_error("variants", index, exc)

    @staticmethod
    def _update_nested_variant(product: Product, item: dict, index: int, key_map: dict) -> ProductVariant:
        variant = (
            ProductVariant.objects.filter(pk=item["id"], product=product).first()
            if item.get("id") is not None
            else None
        )
        if item.get("id") is not None and variant is None:
            raise ValidationError(
                {"variants": {index: {"id": ["This variant does not belong to this product."]}}}
            )
        if variant is None:
            return ProductService._create_nested_variant(product, item, index, key_map)
        fields = {
            key: item[key]
            for key in ("sku", "name", "price", "is_special_edition", "is_active")
            if key in item
        }
        pav_ids = None
        if "options" in item:
            pav_ids = ProductService._resolve_option_refs(
                item["options"], key_map, container="variants", index=index
            )
        try:
            return VariantService.update_variant(
                variant=variant, option_pav_ids=pav_ids, **fields
            )
        except ValidationError as exc:
            raise _indexed_error("variants", index, exc)

    # -- public API ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_product(*, user=None, data: dict) -> Product:
        if isinstance(user, AnonymousUser) or not getattr(user, "is_authenticated", False):
            user = None
        product = Product(
            user=user,
            **{key: data[key] for key in _PRODUCT_SCALAR_FIELDS if key in data},
        )
        
        # Handle feature image
        if "feature_image" in data:
            ImageService.set_image(product, "feature_image", data["feature_image"])
            ImageService.apply_metadata(product, "feature_image", data["feature_image"])
        
        try:
            product.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        product.save()
        # Lock the row so nested variant-combination checks serialize correctly.
        product = Product.objects.select_for_update().get(pk=product.pk)

        key_map: dict[str, ProductAttributeValue] = {}
        for index, item in enumerate(data.get("attribute_values") or []):
            pav = ProductService._create_nested_pav(product, item, index)
            if item.get("key"):
                if item["key"] in key_map:
                    raise ValidationError(
                        {
                            "attribute_values": {
                                index: {"key": ["Duplicate temporary key in this request."]}
                            }
                        }
                    )
                key_map[item["key"]] = pav
        for index, item in enumerate(data.get("variants") or []):
            ProductService._create_nested_variant(product, item, index, key_map)
        return product

    @staticmethod
    @transaction.atomic
    def update_product(*, product: Product, data: dict) -> Product:
        """Partial-safe update. Nested lists are upserted; omitted relations are
        left untouched (never implicitly deleted)."""
        product = Product.objects.select_for_update().get(pk=product.pk)
        for field in _PRODUCT_SCALAR_FIELDS:
            if field in data:
                setattr(product, field, data[field])
        
        # Handle feature image
        if "feature_image" in data:
            old_feature_name = ImageService.set_image(
                product, "feature_image", data["feature_image"]
            )
            ImageService.apply_metadata(product, "feature_image", data["feature_image"])
            # Clean up old image if replaced
            if old_feature_name:
                ImageService.schedule_cleanup([old_feature_name])
        
        try:
            product.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        product.save()

        key_map: dict[str, ProductAttributeValue] = {}
        if "attribute_values" in data:
            for index, item in enumerate(data.get("attribute_values") or []):
                ProductService._update_nested_pav(product, item, index, key_map)
        if "variants" in data:
            for index, item in enumerate(data.get("variants") or []):
                ProductService._update_nested_variant(product, item, index, key_map)
        return product

    @staticmethod
    @transaction.atomic
    def delete_product(*, product: Product) -> None:
        """Delete a product and schedule cleanup of all its Cloudinary images.

        Relations are removed in dependency order first: variant options
        PROTECT their product attribute values, so options, variants, and
        values are deleted explicitly before the product row itself.
        """
        # Collect all image names for cleanup
        names = []
        
        # Product featured image
        if product.feature_image.name:
            names.append(product.feature_image.name)
        
        # Product attribute value images
        names += list(
            ProductAttributeValue.objects.filter(product=product).values_list(
                "feature_image", flat=True
            )
        )
        
        # Additional images
        names += list(
            ProductAttributeImage.objects.filter(
                product_attribute_value__product=product
            ).values_list("image", flat=True)
        )
        
        ProductVariantOption.objects.filter(variant__product=product).delete()
        ProductVariant.objects.filter(product=product).delete()
        ProductAttributeValue.objects.filter(product=product).delete()
        product.delete()
        ImageService.schedule_names_cleanup(names)
