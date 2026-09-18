"""Tab-3 image reads/writes on a product's used values.

- ``listing`` groups the product's ``ProductAttributeValue`` rows by
  attribute with their current images (only values used on the product).
- ``upload_images`` sets the featured image (``null`` clears it) and/or
  appends gallery rows. ``requires_image`` is enforced only when the
  featured image itself is touched, so tab-2's imageless values can gain
  gallery pictures first and a feature image later.
- ``delete_gallery_image`` removes one gallery row (storage cleanup runs
  on commit, like every other image mutation).
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import to_drf_validation_error

from ..models import Product, ProductAttributeImage, ProductAttributeValue
from .images import ImageService


class ProductVariantImagesService:
    @staticmethod
    def listing(*, product: Product) -> dict:
        pavs = (
            ProductAttributeValue.objects.filter(product=product)
            .select_related("attribute", "attribute_value")
            .prefetch_related("additional_images")
            .order_by("attribute__name", "created_at", "id")
        )
        groups: list[dict] = []
        by_attribute: dict[str, dict] = {}
        for pav in pavs:
            key = str(pav.attribute_id)
            group = by_attribute.get(key)
            if group is None:
                group = {"attribute": pav.attribute, "values": []}
                by_attribute[key] = group
                groups.append(group)
            group["values"].append(pav)
        return {"attributes": groups}

    @staticmethod
    @transaction.atomic
    def upload_images(*, product: Product, data: dict) -> ProductAttributeValue:
        pav = (
            ProductAttributeValue.objects.select_for_update()
            .filter(pk=data["value"], product=product)
            .first()
        )
        if pav is None:
            raise ValidationError(
                {"value": ["This value is not used on this product."]}
            )
        if "feature_image" in data:
            old_name = ImageService.set_image(
                pav, "feature_image", data["feature_image"]
            )
            ImageService.apply_metadata(pav, "feature_image", data["feature_image"])
            try:
                pav.full_clean()
            except DjangoValidationError as exc:
                raise to_drf_validation_error(exc)
            pav.save()
            ImageService.schedule_replaced_cleanup(
                old_name, pav.feature_image.name or ""
            )
        if "additional_images" in data:
            ProductVariantImagesService._append_gallery(
                pav, data["additional_images"]
            )
        return (
            ProductAttributeValue.objects.select_related("attribute", "attribute_value")
            .prefetch_related("additional_images")
            .get(pk=pav.pk)
        )

    @staticmethod
    def _append_gallery(pav: ProductAttributeValue, markers) -> None:
        orders = list(
            pav.additional_images.values_list("sort_order", flat=True)
        )
        start = (max(orders) + 1) if orders else 0
        for offset, marker in enumerate(markers or []):
            row = ProductAttributeImage(
                product_attribute_value=pav, sort_order=start + offset
            )
            ImageService.set_image(row, "image", marker)
            row.title = (marker or {}).get("title", "") or ""
            row.caption = (marker or {}).get("caption", "") or ""
            row.alt = (marker or {}).get("alt", "") or ""
            try:
                row.full_clean()
            except DjangoValidationError as exc:
                raise to_drf_validation_error(exc)
            row.save()

    @staticmethod
    @transaction.atomic
    def delete_gallery_image(*, image: ProductAttributeImage) -> None:
        name = image.image.name or ""
        image.delete()
        ImageService.schedule_names_cleanup([name])
