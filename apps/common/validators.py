"""Model-level validators shared across apps."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_key_features(value) -> list[dict]:
    """Validate (and normalize) a product's ``key_features`` JSON value.

    Must be a list of objects, each with a non-empty ``title`` and ``value``.
    Returns the normalized list. Raises ``django.core.exceptions.ValidationError``.
    """
    if not isinstance(value, list):
        raise ValidationError("Key features must be a list.")
    normalized: list[dict] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Key feature #{index} must be an object.")
        title = item.get("title", "")
        feature_value = item.get("value", "")
        if not isinstance(title, str) or not title.strip():
            raise ValidationError(f"Key feature #{index} requires a non-empty 'title'.")
        if not isinstance(feature_value, str) or not feature_value.strip():
            raise ValidationError(f"Key feature #{index} requires a non-empty 'value'.")
        normalized.append({"title": title.strip(), "value": feature_value.strip()})
    return normalized

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def _extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in (name or "") else ""


def validate_image_upload(value):
    """Validate an uploaded image's extension and size (MAX_IMAGE_UPLOAD_MB).

    Only true uploads (``UploadedFile``) are checked: existing storage
    references assigned to model fields (extensionless Cloudinary public_ids
    have no checkable extension/size) pass through — API serializers validate
    upload content at the boundary.
    """
    from django.conf import settings
    from django.core.files.uploadedfile import UploadedFile

    if not isinstance(value, UploadedFile):
        return value

    extension = _extension(getattr(value, "name", ""))
    if extension not in IMAGE_EXTENSIONS:
        raise ValidationError(
            _("Unsupported image format '.%(ext)s'. Allowed: %(allowed)s.")
            % {"ext": extension, "allowed": ", ".join(sorted(IMAGE_EXTENSIONS))},
            code="invalid_extension",
        )
    max_mb = getattr(settings, "MAX_IMAGE_UPLOAD_MB", 5)
    size = getattr(value, "size", 0) or 0
    if size > max_mb * 1024 * 1024:
        raise ValidationError(
            _("Image must be %(max)d MB or smaller.") % {"max": max_mb},
            code="file_too_large",
        )
    return value
