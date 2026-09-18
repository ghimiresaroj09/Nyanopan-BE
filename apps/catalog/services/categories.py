"""Category mutations (image cleanup handled via the image service)."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.common.exceptions import to_drf_validation_error

from ..models import Category
from .images import ImageService

_UNSET: object = object()


class CategoryService:
    @staticmethod
    @transaction.atomic
    def create_category(*, name, slug="", description="", is_active=True, image=_UNSET) -> Category:
        category = Category(name=name, slug=slug or "", description=description, is_active=is_active)
        if image is not _UNSET:
            ImageService.set_image(category, "image", image)
            ImageService.apply_metadata(category, "image", image)
        try:
            category.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        category.save()
        return category

    @staticmethod
    @transaction.atomic
    def update_category(*, category: Category, data: dict) -> Category:
        old_name = category.image.name or ""
        for field in ("name", "slug", "description", "is_active"):
            if field in data:
                setattr(category, field, data[field])
        if "image" in data:
            ImageService.set_image(category, "image", data["image"])
            ImageService.apply_metadata(category, "image", data["image"])
        try:
            category.full_clean()
        except DjangoValidationError as exc:
            raise to_drf_validation_error(exc)
        category.save()
        if "image" in data:
            ImageService.schedule_replaced_cleanup(old_name, category.image.name or "")
        return category

    @staticmethod
    @transaction.atomic
    def delete_category(*, category: Category) -> None:
        name = category.image.name or ""
        category.delete()  # PROTECTed relations raise before any cleanup runs
        ImageService.schedule_names_cleanup([name])
