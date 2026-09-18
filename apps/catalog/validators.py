"""Catalog validators: reusable image-marker validation/normalization.

All catalog images live on the shared Cloudinary/filesystem storage behind
``ImageField``s. API input normalizes to one of three markers per image:
``None`` (clear), ``{"file": <upload>}`` (store a new upload), or
``{"name": <storage name>}`` (reference an existing asset — no storage I/O).
Presentation metadata (title/caption/alt) rides on the marker; delivery URLs
are built from the stored name at read time.
"""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import URLValidator

from apps.catalog.services.images import ImageService

_url_validator = URLValidator()

IMAGE_META_KEYS = ("title", "caption", "alt")


def _coerce_str(value, *, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a string.")
    return value


def _meta(value: dict, label: str) -> dict:
    return {
        key: _coerce_str(value.get(key, ""), label=f"{label} {key}").strip()
        for key in IMAGE_META_KEYS
    }


def _normalize_marker(value: dict, *, label: str) -> dict:
    """Normalize one image dict to a ``{"file"|"name"}`` marker (+ metadata)."""
    if isinstance(value.get("file"), UploadedFile):
        # Pre-validated upload marker (see ImageObjectField): the service
        # stores the file on the model field.
        if value.get("url") or value.get("name") or value.get("public_id"):
            raise ValidationError(f"{label}: provide 'file' on its own, not with a reference.")
        return {"file": value["file"], **_meta(value, label)}
    if "file" in value:
        raise ValidationError(f"{label} file reference must be resolved to an upload first.")

    name = _coerce_str(value.get("name", ""), label=f"{label} name").strip()
    public_id = _coerce_str(value.get("public_id", ""), label=f"{label} public_id").strip()
    if name and public_id and name != public_id:
        raise ValidationError(f"{label}: provide either 'name' or 'public_id', not both.")
    name = name or public_id
    url = _coerce_str(value.get("url", ""), label=f"{label} url").strip()
    if not url and not name:
        raise ValidationError(f"{label} requires a 'url' or 'name'.")
    if url:
        try:
            _url_validator(url)
        except ValidationError:
            raise ValidationError(f"{label} has an invalid URL.")
        extracted = ImageService.reference_name_from_url(url)
        if not extracted:
            raise ValidationError(f"{label} URL is not a usable image reference.")
        if name and name != extracted:
            raise ValidationError(f"{label}: 'name' does not match the 'url'.")
        name = extracted
    elif " " in name or ".." in name.replace("\\", "/").split("/"):
        raise ValidationError(f"{label} has an invalid 'name'.")
    return {"name": name, **_meta(value, label)}


def validate_image_object(value, *, field_label: str = "Image") -> dict | None:
    """Validate and normalize a single image object.

    Accepts ``None``/``""``/``{}`` (clear), a URL string, or a dict with
    ``url``/``name``/``public_id`` plus optional ``title``/``caption``/``alt``
    metadata (or a ``file`` upload marker — see ``ImageObjectField``).

    Returns the normalized marker, or ``None`` when the image is cleared.
    Raises ``django.core.exceptions.ValidationError`` on invalid input.
    """
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        value = {"url": value}
    if not isinstance(value, dict):
        raise ValidationError(f"{field_label} must be an object, a URL string, or null.")

    url = _coerce_str(value.get("url", ""), label=f"{field_label} url").strip()
    name = _coerce_str(value.get("name", "") or value.get("public_id", ""), label=f"{field_label} name").strip()
    meta = _meta(value, field_label)
    if "file" not in value and not url and not name and not any(meta.values()):
        return None
    return _normalize_marker(value, label=field_label)


def validate_additional_images(value) -> list[dict]:
    """Validate and normalize the ``additional_images`` list.

    Each entry must be an object with a valid ``url``/``name`` reference (or
    a ``file`` upload marker) and optional metadata. Returns the normalized
    marker list (``[]`` when blank).
    """
    if value is None or value == "":
        return []
    if not isinstance(value, list):
        raise ValidationError("Additional images must be a list.")
    normalized: list[dict] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Additional image #{index} must be an object.")
        normalized.append(_normalize_marker(item, label=f"Additional image #{index}"))
    return normalized
