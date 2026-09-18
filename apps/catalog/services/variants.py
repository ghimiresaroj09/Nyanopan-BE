"""Variant + variant-option business logic.

Owns the two combination invariants:
1. every option must belong to the variant's product (and be active);
2. a variant holds at most one value per attribute;
3. no two variants of a product may share the same option combination.

All mutating methods run in transactions and lock the product row so
concurrent requests cannot create duplicate combinations.
"""

from collections import defaultdict

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import to_drf_validation_error

from ..models import Product, ProductAttributeValue, ProductVariant, ProductVariantOption
from .sku import generate_sku


class VariantService:
    # -- queries ---------------------------------------------------------------
    @staticmethod
    def get_combination_map(product: Product) -> dict[frozenset[int], int]:
        """Map each variant's option set (PAV ids) to the variant id (2 queries)."""
        grouped: dict[int, set[int]] = defaultdict(set)
        rows = ProductVariantOption.objects.filter(variant__product=product).values_list(
            "variant_id", "product_attribute_value_id"
        )
        for variant_id, pav_id in rows:
            grouped[variant_id].add(pav_id)
        variant_ids = list(product.variants.values_list("id", flat=True))
        return {frozenset(grouped.get(variant_id, set())): variant_id for variant_id in variant_ids}

    # -- validation --------------------------------------------------------------
    @staticmethod
    def validate_option_set(
        *, product: Product, pav_ids: list[int], exclude_variant_id: int | None = None
    ) -> list[ProductAttributeValue]:
        """Validate a candidate option set for a (new or existing) variant.

        Returns the ordered ``ProductAttributeValue`` rows. Raises DRF
        ``ValidationError`` with an ``options`` key on any violation.
        """
        if not pav_ids:
            raise ValidationError({"options": ["At least one option is required."]})
        if len(set(pav_ids)) != len(pav_ids):
            raise ValidationError({"options": ["Duplicate options are not allowed."]})

        pavs = list(
            ProductAttributeValue.objects.select_related("attribute", "attribute_value").filter(
                pk__in=pav_ids
            )
        )
        if len(pavs) != len(set(pav_ids)):
            raise ValidationError({"options": ["One or more options are invalid."]})
        by_id = {pav.id: pav for pav in pavs}

        for pav_id in pav_ids:
            pav = by_id[pav_id]
            if pav.product_id != product.id:
                raise ValidationError(
                    {"options": ["Every option must belong to the same product as the variant."]}
                )
            if not pav.is_active:
                raise ValidationError(
                    {"options": [f"Option '{pav}' is not active."]}
                )

        attribute_ids = [by_id[pav_id].attribute_id for pav_id in pav_ids]
        if len(set(attribute_ids)) != len(attribute_ids):
            raise ValidationError(
                {"options": ["Only one value per attribute is allowed in a variant."]}
            )

        key = frozenset(pav_ids)
        existing_variant_id = VariantService.get_combination_map(product).get(key)
        if existing_variant_id is not None and existing_variant_id != exclude_variant_id:
            raise ValidationError(
                {
                    "options": [
                        "This exact combination already exists for another variant of this product."
                    ]
                }
            )
        return [by_id[pav_id] for pav_id in pav_ids]

    # -- mutations ---------------------------------------------------------------
    @staticmethod
    def _lock_product(product_id: int) -> Product:
        return Product.objects.select_for_update().get(pk=product_id)

    @staticmethod
    @transaction.atomic
    def create_variant(
        *,
        product: Product,
        price,
        option_pav_ids: list[int],
        sku: str = "",
        name: str = "",
        is_special_edition: bool = False,
        is_active: bool = True,
    ) -> ProductVariant:
        product = VariantService._lock_product(product.pk)
        pavs = VariantService.validate_option_set(product=product, pav_ids=list(option_pav_ids))
        sku = (sku or "").strip()
        if not sku:
            sku = generate_sku(product, pavs)
        variant = ProductVariant(
            product=product,
            sku=sku,
            name=name,
            price=price,
            is_special_edition=is_special_edition,
            is_active=is_active,
        )
        try:
            variant.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        variant.save()
        ProductVariantOption.objects.bulk_create(
            [
                ProductVariantOption(variant=variant, product_attribute_value=pav)
                for pav in pavs
            ]
        )
        return variant

    @staticmethod
    @transaction.atomic
    def update_variant(
        *,
        variant: ProductVariant,
        option_pav_ids: list[int] | None = None,
        **fields,
    ) -> ProductVariant:
        """Update scalar fields; replace options only when ``option_pav_ids`` is given."""
        product = VariantService._lock_product(variant.product_id)
        variant.product = product
        for name, value in fields.items():
            setattr(variant, name, value)
        pavs = None
        if option_pav_ids is not None:
            pavs = VariantService.validate_option_set(
                product=product,
                pav_ids=list(option_pav_ids),
                exclude_variant_id=variant.pk,
            )
        try:
            variant.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        variant.save()
        if pavs is not None:
            current_ids = set(
                variant.options.values_list("product_attribute_value_id", flat=True)
            )
            new_ids = {pav.id for pav in pavs}
            if current_ids != new_ids:
                variant.options.exclude(product_attribute_value_id__in=new_ids).delete()
                ProductVariantOption.objects.bulk_create(
                    [
                        ProductVariantOption(variant=variant, product_attribute_value=pav)
                        for pav in pavs
                        if pav.id not in current_ids
                    ]
                )
        return variant

    @staticmethod
    @transaction.atomic
    def add_option(*, variant: ProductVariant, pav_id: int) -> ProductVariantOption:
        product = VariantService._lock_product(variant.product_id)
        current_ids = list(
            variant.options.values_list("product_attribute_value_id", flat=True)
        )
        if pav_id in current_ids:
            raise ValidationError(
                {"product_attribute_value": ["This option is already on the variant."]}
            )
        VariantService.validate_option_set(
            product=product,
            pav_ids=[*current_ids, pav_id],
            exclude_variant_id=variant.pk,
        )
        return ProductVariantOption.objects.create(
            variant=variant, product_attribute_value_id=pav_id
        )

    @staticmethod
    @transaction.atomic
    def change_option(*, option: ProductVariantOption, new_pav_id: int) -> ProductVariantOption:
        variant = option.variant
        product = VariantService._lock_product(variant.product_id)
        current_ids = [
            pav_id
            for pav_id in variant.options.values_list(
                "product_attribute_value_id", flat=True
            )
            if pav_id != option.product_attribute_value_id
        ]
        VariantService.validate_option_set(
            product=product,
            pav_ids=[*current_ids, new_pav_id],
            exclude_variant_id=variant.pk,
        )
        option.product_attribute_value_id = new_pav_id
        try:
            option.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        option.save(update_fields=["product_attribute_value"])
        return option

    @staticmethod
    @transaction.atomic
    def remove_option(*, option: ProductVariantOption) -> None:
        variant = option.variant
        product = VariantService._lock_product(variant.product_id)
        remaining_ids = [
            pav_id
            for pav_id in variant.options.values_list(
                "product_attribute_value_id", flat=True
            )
            if pav_id != option.product_attribute_value_id
        ]
        # Removing an option must neither empty the variant nor duplicate a sibling.
        VariantService.validate_option_set(
            product=product,
            pav_ids=remaining_ids,
            exclude_variant_id=variant.pk,
        )
        option.delete()
