"""Tab-2 variant save: resolve the attribute palette, upsert variants by SKU.

The frontend generates every combination client-side and POSTs the whole
batch. This service (atomically):

1. resolves each palette entry to ``Attribute`` / ``AttributeValue`` rows,
   creating the product's ``ProductAttributeValue`` rows (imageless — tab 3
   adds pictures later, so ``requires_image`` is deliberately not enforced
   here);
2. upserts each generated variant by SKU within the product (same SKU updates
   price/name/flags/options, new SKU creates), reusing ``VariantService`` so
   all combination invariants still hold.

Returns plain data for ``ProductVariantValuesResponseSerializer``.

``bulk_update_variants`` (PATCH) is the slim update-only counterpart: rows
are keyed by SKU, only the sent scalar fields change, options stay as-is,
and unknown SKUs fail the whole request atomically (nothing is created).
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError

from ..models import (
    Attribute,
    AttributeValue,
    Product,
    ProductAttributeValue,
    ProductVariant,
)
from .variants import VariantService


class ProductVariantValuesService:
    @staticmethod
    @transaction.atomic
    def save_variants(
        *, product: Product, attributes: list, generatedVarients: list
    ) -> dict:
        product = Product.objects.select_for_update().get(pk=product.pk)
        palette = ProductVariantValuesService._ensure_palette(
            product=product, entries=attributes
        )
        variants = ProductVariantValuesService._upsert_variants(
            product=product, items=generatedVarients
        )
        return {"attributes": palette, "generatedVarients": variants}

    @staticmethod
    @transaction.atomic
    def bulk_update_variants(*, product: Product, generatedVarients: list) -> dict:
        """Bulk-update variant scalars by SKU; unknown SKUs fail atomically.

        Each row selects one of the product's variants by SKU and changes
        only the sent fields (name/price/flags); options stay as-is and
        nothing is ever created here.
        """
        product = Product.objects.select_for_update().get(pk=product.pk)
        seen: dict[str, int] = {}
        duplicates: dict[int, dict] = {}
        for index, item in enumerate(generatedVarients):
            sku = item["sku"]
            if sku in seen:
                duplicates[index] = {
                    "sku": [f"Duplicate SKU in this request: {sku}."]
                }
            else:
                seen[sku] = index
        if duplicates:
            raise ValidationError({"generatedVarients": duplicates})

        by_sku = {
            variant.sku: variant
            for variant in ProductVariant.objects.select_for_update().filter(
                product=product, sku__in=list(seen)
            )
        }
        errors: dict[int, dict] = {}
        for index, item in enumerate(generatedVarients):
            if item["sku"] in by_sku:
                continue
            if ProductVariant.objects.filter(sku=item["sku"]).exists():
                errors[index] = {
                    "sku": ["This SKU is already used by another product."]
                }
            else:
                errors[index] = {"sku": [f"Unknown SKU: {item['sku']}."]}
        if errors:
            raise ValidationError({"generatedVarients": errors})

        updated = []
        for index, item in enumerate(generatedVarients):
            fields = {
                field: item[field]
                for field in ("name", "price", "is_active", "is_special_edition")
                if field in item
            }
            try:
                updated.append(
                    VariantService.update_variant(
                        variant=by_sku[item["sku"]], **fields
                    )
                )
            except ValidationError as exc:
                raise ValidationError({"generatedVarients": {index: exc.detail}})
        by_id = {
            str(variant.id): variant
            for variant in ProductVariant.objects.filter(
                pk__in=[variant.pk for variant in updated]
            ).prefetch_related("options__product_attribute_value")
        }
        return {
            "attributes": ProductVariantValuesService._stored_palette(
                product=product
            ),
            "generatedVarients": [by_id[str(variant.id)] for variant in updated],
        }

    @staticmethod
    def _stored_palette(*, product: Product) -> list:
        """The product's current palette, grouped by attribute name."""
        groups: dict[str, dict] = {}
        pavs = (
            ProductAttributeValue.objects.filter(product=product)
            .select_related("attribute", "attribute_value")
            .order_by("attribute__name", "attribute_value__name")
        )
        for pav in pavs:
            key = str(pav.attribute_id)
            group = groups.setdefault(
                key, {"attribute": pav.attribute, "options": []}
            )
            group["options"].append(pav.attribute_value)
        return list(groups.values())

    # -- palette ------------------------------------------------------------
    @staticmethod
    def _ensure_palette(*, product: Product, entries: list) -> list:
        attribute_ids = {str(entry["attribute"]) for entry in entries}
        value_ids = {
            str(option) for entry in entries for option in entry["options"]
        }
        known_attributes = {
            str(attribute.id): attribute
            for attribute in Attribute.objects.filter(pk__in=attribute_ids)
        }
        known_values = {
            str(value.id): value
            for value in AttributeValue.objects.filter(pk__in=value_ids)
        }
        errors: dict[int, dict] = {}
        for index, entry in enumerate(entries):
            attribute_id = str(entry["attribute"])
            attribute = known_attributes.get(attribute_id)
            if attribute is None:
                errors[index] = {"attribute": ["Invalid attribute id."]}
                continue
            bad = [
                str(option)
                for option in entry["options"]
                if str(option) not in known_values
            ]
            if bad:
                errors[index] = {
                    "options": [f"Invalid attribute value id: {value}." for value in bad]
                }
                continue
            foreign = sorted(
                {
                    str(option)
                    for option in entry["options"]
                    if str(known_values[str(option)].attribute_id) != attribute_id
                }
            )
            if foreign:
                errors[index] = {
                    "options": [
                        f"Option {value} does not belong to attribute {attribute.name}."
                        for value in foreign
                    ]
                }
        if errors:
            raise ValidationError({"attributes": errors})

        palette = []
        for entry in entries:
            attribute = known_attributes[str(entry["attribute"])]
            options = []
            for option_id in entry["options"]:
                value = known_values[str(option_id)]
                ProductAttributeValue.objects.get_or_create(
                    product=product, attribute=attribute, attribute_value=value
                )
                options.append(value)
            palette.append({"attribute": attribute, "options": options})
        return palette

    # -- variants -----------------------------------------------------------
    @staticmethod
    def _upsert_variants(*, product: Product, items: list) -> list:
        seen_skus: dict[str, int] = {}
        duplicates: dict[int, dict] = {}
        for index, item in enumerate(items):
            sku = (item.get("sku") or "").strip()
            if not sku:
                continue
            if sku in seen_skus:
                duplicates[index] = {
                    "sku": [f"Duplicate SKU in this request: {sku}."]
                }
            else:
                seen_skus[sku] = index
        if duplicates:
            raise ValidationError({"generatedVarients": duplicates})

        variants = []
        for index, item in enumerate(items):
            try:
                variants.append(
                    ProductVariantValuesService._upsert_one(
                        product=product, item=item
                    )
                )
            except ValidationError as exc:
                raise ValidationError({"generatedVarients": {index: exc.detail}})
        # Prefetch options for the response echo, keeping request order.
        by_id = {
            str(variant.id): variant
            for variant in ProductVariant.objects.filter(
                pk__in=[variant.pk for variant in variants]
            ).prefetch_related("options__product_attribute_value")
        }
        return [by_id[str(variant.id)] for variant in variants]

    @staticmethod
    def _upsert_one(*, product: Product, item: dict) -> ProductVariant:
        value_attributes = {
            str(value_id): str(block["attributeId"])
            for block in item["attributes"]
            for value_id in block["attributeValues"]
        }
        pav_ids = []
        for option_id in item["optionIds"]:
            pav, _ = ProductAttributeValue.objects.get_or_create(
                product=product,
                attribute_id=value_attributes[str(option_id)],
                attribute_value_id=option_id,
            )
            pav_ids.append(pav.pk)
        fields = {
            "name": item.get("name", ""),
            "price": item["price"],
            "is_active": item.get("is_active", True),
            "is_special_edition": item.get("is_special_edition", False),
        }
        sku = (item.get("sku") or "").strip()
        if not sku:
            return VariantService.create_variant(
                product=product, sku="", option_pav_ids=pav_ids, **fields
            )
        existing = ProductVariant.objects.filter(sku=sku).first()
        if existing is not None and existing.product_id != product.id:
            raise ValidationError(
                {"sku": ["This SKU is already used by another product."]}
            )
        if existing is None:
            return VariantService.create_variant(
                product=product, sku=sku, option_pav_ids=pav_ids, **fields
            )
        return VariantService.update_variant(
            variant=existing, option_pav_ids=pav_ids, **fields
        )
