"""Reusable custom serializer fields."""

import base64
import binascii
import json
import re
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.validators import validate_additional_images, validate_image_object
from apps.common.validators import validate_image_upload, validate_key_features

IMAGE_OBJECT_SCHEMA = {
    "type": "object",
    "nullable": True,
    "description": (
        "Single image. Responses return the delivery URL plus metadata; "
        "requests reference an existing asset with url, name, or public_id "
        "(or a file marker in multipart writes), or null to clear."
    ),
    "properties": {
        "url": {
            "type": "string",
            "format": "uri",
            "description": "Delivery URL (responses); accepted in requests to reference that asset.",
            "example": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-main.jpg",
        },
        "public_id": {
            "type": "string",
            "description": "Stored asset name. Returned in responses; accepted in requests for round-trips.",
            "example": "shop/grey-main",
        },
        "name": {
            "type": "string",
            "writeOnly": True,
            "description": "Request-only alias of public_id: reference an existing asset by name.",
            "example": "shop/grey-main",
        },
        "file": {
            "type": "string",
            "writeOnly": True,
            "description": (
                "Request-only image source: the name of a multipart file part "
                "holding the binary (top-level multipart sends the binary "
                "itself), or a 'data:image/...;base64,...' URI to upload the "
                "image inline inside a JSON request."
            ),
            "example": "grey-img",
        },
        "title": {"type": "string", "example": "Grey Celsi Slippers"},
        "caption": {"type": "string", "example": "Grey wool felt slippers"},
        "alt": {"type": "string", "example": "Grey slippers"},
    },
}

PUBLIC_IMAGE_OBJECT_SCHEMA = {
    "type": "object",
    "nullable": True,
    "description": "Single image (public payloads omit the internal asset name).",
    "properties": {
        "url": {
            "type": "string",
            "format": "uri",
            "example": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-main.jpg",
        },
        "title": {"type": "string", "example": "Grey Celsi Slippers"},
        "caption": {"type": "string", "example": "Grey wool felt slippers"},
        "alt": {"type": "string", "example": "Grey slippers"},
    },
}


def _validate_uploaded_image(label: str, uploaded_file):
    """Pillow + extension/size validation for a directly uploaded file."""
    serializers.ImageField().run_validation(uploaded_file)
    try:
        return validate_image_upload(uploaded_file)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages)


def _field_context(field) -> dict:
    try:
        context = field.context
    except AttributeError:
        return {}
    return context if isinstance(context, dict) else {}


_DATA_URI_RE = re.compile(r"^data:(image/[A-Za-z0-9.+-]+);base64,(.+)$", re.DOTALL)
_DATA_URI_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def _upload_from_data_uri(label: str, uri: str):
    """Decode a ``data:image/...;base64,...`` URI into a validated upload.

    Same Pillow + extension + size validation as a multipart file, so JSON
    clients can attach images in a single request (no pre-upload needed).
    """
    match = _DATA_URI_RE.match(uri.strip())
    if not match:
        raise serializers.ValidationError(
            {"file": ["Must be the name of an uploaded file part or a 'data:image/...;base64,...' URI."]}
        )
    mime, payload = match.group(1).lower(), match.group(2).strip()
    ext = _DATA_URI_EXTENSIONS.get(mime)
    if ext is None:
        raise serializers.ValidationError(
            {"file": [f"Unsupported image type '{mime}'. Allowed: png, jpg, webp, gif."]}
        )
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        raise serializers.ValidationError({"file": ["Invalid base64 image data."]})
    if not raw:
        raise serializers.ValidationError({"file": ["Invalid base64 image data."]})
    upload = SimpleUploadedFile(f"upload.{ext}", raw, content_type=mime)
    return _validate_uploaded_image(label, upload)


def _resolve_file_reference(label: str, context: dict, data: dict) -> dict:
    """Resolve a ``{"file": ...}`` marker to an uploaded file.

    Accepts a multipart part name (``{"file": "grey-img"}`` plus a
    ``grey-img`` file part) or an inline base64 data URI
    (``{"file": "data:image/png;base64,..."}``) for pure-JSON writes.
    """
    part = data.get("file")
    if not isinstance(part, str) or not part.strip():
        raise serializers.ValidationError({"file": ["Must be the name of an uploaded file part."]})
    part = part.strip()
    if part.startswith("data:"):
        return {**data, "file": _upload_from_data_uri(label, part)}
    request = context.get("request")
    files = getattr(request, "FILES", {}) or {}
    if part not in files:
        raise serializers.ValidationError(
            {"file": [f"No uploaded file part named '{part}'. Send multipart/form-data with a '{part}' file part."]}
        )
    upload = _validate_uploaded_image(label, files[part])
    return {**data, "file": upload}


@extend_schema_field(IMAGE_OBJECT_SCHEMA)
class ImageObjectField(serializers.Field):
    """Nested image object spanning an ImageField plus metadata columns.

    Declared under the image attribute name (``image`` / ``feature_image``);
    representation is built from the whole model instance.

    Read: ``{"url", "public_id", "title", "caption", "alt"}`` (or ``None``),
    with the URL built from the stored asset name.
    Write: ``null``/``""`` clears, a URL string references that asset, a
    ``{"name"/"public_id"}`` object references an existing asset — or upload
    a file directly:

    - multipart part: pass the binary file itself as the field value;
    - nested payloads: ``{"file": "<part-name>", ...metadata}`` referencing a
      file part of the same multipart request (stored on the model field by
      the service layer).
    """

    default_error_messages = {"invalid": "Invalid image value."}

    def __init__(self, *, prefix: str, include_public_id: bool = True, **kwargs):
        self.prefix = prefix
        self.include_public_id = include_public_id
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        # Representation needs several model fields, so pass the instance through.
        return instance

    def to_representation(self, obj) -> dict | None:
        field_file = getattr(obj, self.prefix, None)
        name = getattr(field_file, "name", "") or ""
        if not name:
            return None
        try:
            url = field_file.url
        except ValueError:
            return None
        request = _field_context(self).get("request")
        if url.startswith("/") and request is not None:
            url = request.build_absolute_uri(url)
        data = {
            "url": url,
            "title": getattr(obj, f"{self.prefix}_title", "") or "",
            "caption": getattr(obj, f"{self.prefix}_caption", "") or "",
            "alt": getattr(obj, f"{self.prefix}_alt", "") or "",
        }
        if self.include_public_id:
            data["public_id"] = name
        return data

    def to_internal_value(self, data) -> dict | None:
        if isinstance(data, UploadedFile):
            data = {"file": _validate_uploaded_image(self.prefix, data)}
        elif isinstance(data, dict) and "file" in data:
            data = _resolve_file_reference(self.prefix, _field_context(self), data)
        try:
            return validate_image_object(data, field_label=self.prefix)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


@extend_schema_field(PUBLIC_IMAGE_OBJECT_SCHEMA)
class PublicImageObjectField(ImageObjectField):
    """ImageObjectField without public_id (public category payloads)."""

    def __init__(self, *args, **kwargs):
        kwargs["include_public_id"] = False
        super().__init__(*args, **kwargs)


@extend_schema_field({"type": "array", "items": {**IMAGE_OBJECT_SCHEMA, "nullable": False}})
class AdditionalImagesField(serializers.Field):
    """List of image objects for ``additional_images``.

    Accepts URL objects (JSON), binary files (repeat the multipart part, or
    pass ``{"file": "<part-name>"}`` items inside nested payloads), or a
    JSON-encoded list string in multipart requests.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def get_value(self, dictionary):
        if hasattr(dictionary, "getlist"):
            values = dictionary.getlist(self.field_name, [])
            if values and all(isinstance(item, UploadedFile) for item in values):
                return list(values)
        return super().get_value(dictionary)

    def to_representation(self, value) -> list:
        images = value.all() if hasattr(value, "all") else (value or [])
        request = _field_context(self).get("request")
        items = []
        for image in images:
            name = getattr(getattr(image, "image", None), "name", "") or ""
            if not name:
                continue
            try:
                url = image.image.url
            except ValueError:
                continue
            if url.startswith("/") and request is not None:
                url = request.build_absolute_uri(url)
            items.append(
                {
                    "url": url,
                    "public_id": name,
                    "title": image.title or "",
                    "caption": image.caption or "",
                    "alt": image.alt or "",
                }
            )
        return items

    def to_internal_value(self, data) -> list:
        if isinstance(data, str) and data.strip():
            try:
                data = json.loads(data)
            except ValueError:
                raise serializers.ValidationError("Must be a list of image objects.")
        if isinstance(data, (list, tuple)):
            items = []
            for item in data:
                if isinstance(item, UploadedFile):
                    upload = _validate_uploaded_image("additional image", item)
                    items.append({"file": upload})
                elif isinstance(item, dict) and "file" in item:
                    items.append(_resolve_file_reference("additional image", _field_context(self), item))
                else:
                    items.append(item)
            data = items
        try:
            return validate_additional_images(data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


@extend_schema_field(
    {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["title", "value"],
            "properties": {"title": {"type": "string"}, "value": {"type": "string"}},
        },
    }
)
class KeyFeaturesField(serializers.Field):
    """Validated ``key_features`` JSON array."""

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_representation(self, value) -> list:
        return list(value or [])

    def to_internal_value(self, data) -> list:
        try:
            return validate_key_features(data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


@extend_schema_field(
    {
        "description": (
            "Variant-option reference: an existing value UUID, a temporary key "
            "created in the same request, or an explicit {id} / {key} object."
        ),
        "oneOf": [
            {
                "type": "string",
                "format": "uuid",
                "example": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            },
            {"type": "string", "example": "grey"},
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "key": {"type": "string"},
                },
                "example": {"key": "grey"},
            },
        ],
    }
)
class OptionReferenceField(serializers.Field):
    """A variant-option reference in nested writes.

    Accepts a product-attribute-value UUID, a temp key created in the same
    request (``"grey"``), or an explicit object (``{"id": "<uuid>"}`` /
    ``{"key": "grey"}``). Normalizes to ``{"id": UUID}`` / ``{"key": ...}``.
    """

    default_error_messages = {
        "invalid": "Each option must be a UUID, a temporary key, or an {id|key} object."
    }

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if isinstance(data, bool):
            self.fail("invalid")
        if isinstance(data, UUID):
            return {"id": data}
        if isinstance(data, str) and data.strip():
            text = data.strip()
            try:
                return {"id": UUID(text)}
            except ValueError:
                return {"key": text}
        if isinstance(data, dict):
            raw_id = data.get("id")
            if isinstance(raw_id, UUID):
                return {"id": raw_id}
            if isinstance(raw_id, str) and raw_id.strip():
                try:
                    return {"id": UUID(raw_id.strip())}
                except ValueError:
                    pass
            raw_key = data.get("key")
            if isinstance(raw_key, str) and raw_key.strip():
                return {"key": raw_key.strip()}
        self.fail("invalid")


class FlexibleRelatedField(serializers.PrimaryKeyRelatedField):
    """UUID-or-human-key reference (writes accept either; reads still return UUIDs).

    ``lookup_field`` is the human key tried when the input is not a UUID: a
    slug (categories, models, products), a name (attributes), or a SKU
    (variants). Matching is exact-first with a single-match
    case-insensitive fallback (slugs also try the slugified input), so
    ``"slippers"`` and ``"Color"`` resolve without copying UUIDs.
    """

    def __init__(self, *args, lookup_field: str, lookup_label: str = "", **kwargs):
        self.lookup_field = lookup_field
        self.lookup_label = lookup_label or lookup_field
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str) and data.strip():
            text = data.strip()
            try:
                UUID(text)
            except ValueError:
                return self._by_human_key(text)
        return super().to_internal_value(data)

    def _by_human_key(self, text: str):
        queryset = self.get_queryset()
        label = queryset.model._meta.verbose_name
        candidates = [text]
        if self.lookup_field == "slug":
            slug = slugify(text)
            if slug and slug != text:
                candidates.append(slug)
        elif self.lookup_field == "code":
            candidates = [text.upper()]
        for candidate in candidates:
            obj = queryset.filter(**{self.lookup_field: candidate}).first()
            if obj is not None:
                return obj
        matches = list(queryset.filter(**{f"{self.lookup_field}__iexact": text})[:2])
        if len(matches) > 1:
            raise serializers.ValidationError(
                f"Multiple {queryset.model._meta.verbose_name_plural} match "
                f"'{text}'. Pass the UUID to be exact."
            )
        if matches:
            return matches[0]
        raise serializers.ValidationError(
            f"No {label} found for '{text}'. Pass the UUID or the {self.lookup_label}."
        )


VALUE_NAME_MARKER = "__value_name"


class AttributeValueNameField(serializers.PrimaryKeyRelatedField):
    """Attribute-value reference: a UUID, or a name resolved within the attribute.

    Plain names cannot be resolved here (the attribute is a sibling field),
    so they are returned as ``{"__value_name": <name>}`` markers that the
    serializer's ``validate()`` resolves against the chosen attribute.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.strip():
            text = data.strip()
            try:
                UUID(text)
            except ValueError:
                return {VALUE_NAME_MARKER: text}
        return super().to_internal_value(data)
