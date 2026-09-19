"""Attribute + attribute-value business logic."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import to_drf_validation_error

from ..models import Attribute, AttributeValue


class AttributeValueService:
    """Bulk creation of attribute values (all-or-nothing)."""

    @staticmethod
    @transaction.atomic
    def bulk_create(*, attribute, names: list[str]) -> list[AttributeValue]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        if duplicates:
            raise ValidationError(
                {
                    "value": [
                        f"Duplicate value in this request: {name!r}."
                        for name in sorted(duplicates)
                    ]
                }
            )
        existing = set(
            AttributeValue.objects.filter(attribute=attribute, name__in=names).values_list(
                "name", flat=True
            )
        )
        if existing:
            raise ValidationError(
                {
                    "value": [
                        "Already exists for this attribute: "
                        + ", ".join(sorted(existing))
                        + "."
                    ]
                }
            )
        return AttributeValue.objects.bulk_create(
            [AttributeValue(attribute=attribute, name=name) for name in names]
        )

    @staticmethod
    @transaction.atomic
    def ensure_values(*, attribute, names: list[str]) -> list[AttributeValue]:
        """Create the missing names; existing ones are left untouched.

        Used by attribute updates (``{"value": [...]}`` means "make sure
        these exist"). Returns the newly created rows.
        """
        ordered = list(dict.fromkeys(names))
        existing = set(
            AttributeValue.objects.filter(
                attribute=attribute, name__in=ordered
            ).values_list("name", flat=True)
        )
        missing = [name for name in ordered if name not in existing]
        if not missing:
            return []
        return AttributeValue.objects.bulk_create(
            [AttributeValue(attribute=attribute, name=name) for name in missing]
        )


class AttributeService:
    """Attribute mutations, with optional nested ``value`` names."""

    @staticmethod
    @transaction.atomic
    def create_attribute(*, data: dict, value_names=None) -> Attribute:
        attribute = Attribute(**data)
        try:
            attribute.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        attribute.save()
        if value_names:
            AttributeValueService.bulk_create(
                attribute=attribute, names=list(value_names)
            )
        return attribute

    @staticmethod
    @transaction.atomic
    def update_attribute(*, attribute: Attribute, data: dict, value_names=None) -> Attribute:
        for field in ("name", "requires_image", "is_active"):
            if field in data:
                setattr(attribute, field, data[field])
        try:
            attribute.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        attribute.save()
        if value_names is not None:
            # Replace all values: delete removed ones, add new ones, keep existing
            value_names_list = list(value_names)
            value_names_set = set(value_names_list)
            
            # Get all current values for this attribute
            existing_values = AttributeValue.objects.filter(attribute=attribute)
            
            # Delete values that are no longer in the list
            to_delete = existing_values.exclude(name__in=value_names_set)
            to_delete.delete()
            
            # Add new values that don't exist yet (same as before)
            AttributeValueService.ensure_values(
                attribute=attribute, names=value_names_list
            )
        return attribute
