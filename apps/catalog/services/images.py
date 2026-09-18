"""Image uploads: Cloudinary with a local filesystem fallback.

Every catalog image is an ``ImageField`` on the shared storage
(``apps.common.storages.image_storage``): the database keeps the asset name
and ``field.url`` builds the delivery URL. Serializers hand the services one
of three markers per image — ``None`` (clear), ``{"file": <upload>}``, or
``{"name": <storage name>}`` — and the helpers below assign those markers
onto model fields.

Cleanup of a replaced or removed asset is always scheduled with
``transaction.on_commit`` so a failed database write can never lose the
existing image, and a successful write does not leave orphaned assets behind.
"""

import logging
import re
import uuid
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from PIL import Image
from rest_framework.exceptions import ValidationError

from apps.common.storages import image_storage
from apps.common.validators import IMAGE_EXTENSIONS

logger = logging.getLogger(__name__)

# Matches the storable name inside a Cloudinary delivery URL, e.g.
# https://res.cloudinary.com/demo/image/upload/v169/folder/grey.jpg -> folder/grey
_CLOUDINARY_URL_RE = re.compile(
    r"^https?://res\.cloudinary\.com/[^/]+/image/upload/(?:v\d+/)?(.+?)(?:\.[A-Za-z0-9]+)?$"
)

# Characters allowed in the (optional) upload folder parameter.
_FOLDER_CHARS_RE = re.compile(r"[^A-Za-z0-9/_-]+")


class ImageService:
    @staticmethod
    def use_cloudinary() -> bool:
        return bool(getattr(settings, "USE_CLOUDINARY", False))

    # -- uploads / deletions ---------------------------------------------------
    @staticmethod
    def upload_image(uploaded_file, *, folder: str | None = None) -> dict:
        """Store an image via the active backend. Returns public_id/url (+ dimensions).

        ``public_id`` is the Cloudinary public_id (cloud mode) or the stored
        relative name (filesystem mode) — assign it to an ``ImageField`` (or
        pass it back to ``delete_image``). The standalone ``/images/upload/``
        endpoint is the only direct caller; catalog writes go through model
        fields instead.
        """
        width, height, img_format = ImageService._read_dimensions(uploaded_file)
        name = ImageService._build_name(uploaded_file, folder, img_format)
        try:
            storage = image_storage()
            saved_name = storage.save(name, uploaded_file)
            url = storage.url(saved_name)
        except ImproperlyConfigured as exc:
            raise ValidationError(f"Image upload failed: {exc}") from exc
        except ValidationError:
            raise
        except Exception as exc:  # noqa: BLE001 - surfaced as API error
            logger.exception("Image upload failed.")
            # Admin-only endpoint: surfacing the upstream message aids debugging.
            detail = str(exc).strip() or "Please try again."
            raise ValidationError(f"Image upload failed: {detail}") from exc
        return {
            "public_id": saved_name,
            "url": url,
            "width": width,
            "height": height,
            "format": img_format,
        }

    @staticmethod
    def delete_image(public_id: str) -> bool:
        """Delete an asset from the active backend. Never raises; returns success flag."""
        if not (public_id or "").strip():
            return False
        if ImageService.use_cloudinary():
            try:
                return bool(image_storage().delete(public_id.strip()))
            except Exception:  # noqa: BLE001 - cleanup must never break requests
                logger.exception("Cloudinary delete failed for %s.", public_id)
                return False
        # Filesystem mode: public_id is the stored relative name.
        name = public_id.strip().lstrip("/")
        if not name or ".." in name.replace("\\", "/").split("/"):
            logger.warning("Refusing to delete suspicious local asset name: %r.", public_id)
            return False
        try:
            storage = image_storage()
            if not storage.exists(name):
                return False
            storage.delete(name)
            return True
        except Exception:  # noqa: BLE001 - cleanup must never break requests
            logger.exception("Local image delete failed for %s.", public_id)
            return False

    @staticmethod
    def schedule_delete(public_id: str | None) -> None:
        """Delete an asset only after the surrounding transaction commits."""
        if not public_id:
            return
        transaction.on_commit(lambda: ImageService.delete_image(public_id))

    @staticmethod
    def reference_name_from_url(url: str) -> str:
        """Best-effort Cloudinary delivery URL (or /media/ URL) -> storage name.

        Returns ``""`` when the value is not a usable storage reference.
        """
        text = (url or "").strip()
        match = _CLOUDINARY_URL_RE.match(text)
        if match:
            return match.group(1)
        if text.startswith("/media/"):
            return text[len("/media/") :]
        if "://" in text or " " in text or text.startswith("data:"):
            return ""
        return text

    # -- ImageField assignment ---------------------------------------------------
    @staticmethod
    def set_image(instance, field_name: str, marker: dict | None) -> str:
        """Assign an image ``marker`` to an ``ImageField``; returns the old name.

        ``marker`` is ``None`` (clear the field), ``{"file": <upload>}`` (store
        a new upload), or ``{"name": <storage name>}`` (reference an existing
        asset — no storage I/O). Presentation metadata (title/caption/alt) is
        applied by the caller.
        """
        field_file = getattr(instance, field_name)
        old_name = field_file.name or ""
        if marker is None:
            setattr(instance, field_name, "")
            return old_name
        if "file" in marker:
            upload = marker["file"]
            if not hasattr(upload, "read"):
                raise ValidationError("Invalid image file.")
            field_file.save(upload.name, upload, save=False)
            return old_name
        setattr(instance, field_name, marker.get("name", "") or "")
        return old_name

    @staticmethod
    def apply_metadata(instance, prefix: str, marker: dict | None) -> None:
        """Apply an image marker's title/caption/alt onto ``<prefix>_*`` columns."""
        marker = marker or {}
        setattr(instance, f"{prefix}_title", marker.get("title", "") or "")
        setattr(instance, f"{prefix}_caption", marker.get("caption", "") or "")
        setattr(instance, f"{prefix}_alt", marker.get("alt", "") or "")

    @staticmethod
    def schedule_replaced_cleanup(old_name: str, new_name: str) -> None:
        """Schedule deletion of a replaced single image (if its asset changed)."""
        if old_name and old_name != (new_name or ""):
            ImageService.schedule_delete(old_name)

    @staticmethod
    def schedule_names_cleanup(names) -> None:
        """Schedule deletion of every listed asset name (falsy entries skipped)."""
        for name in names or []:
            ImageService.schedule_delete(name)

    # -- upload helpers ----------------------------------------------------------
    @staticmethod
    def _clean_folder(folder: str | None) -> str:
        cleaned = _FOLDER_CHARS_RE.sub("", folder or "").strip("/")
        parts = [part for part in cleaned.split("/") if part not in ("", ".", "..")]
        return "/".join(parts) or "ecommerce"

    @staticmethod
    def _build_name(uploaded_file, folder: str | None, img_format: str) -> str:
        original = getattr(uploaded_file, "name", "") or ""
        ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
        if ext not in IMAGE_EXTENSIONS:
            # The serializer normally guarantees an allowed extension; fall back
            # to the detected format (or png) so storage always gets a sane name.
            ext = img_format if img_format in IMAGE_EXTENSIONS else "png"
        clean_folder = ImageService._clean_folder(
            folder or getattr(settings, "CLOUDINARY_UPLOAD_FOLDER", "")
        )
        return f"{clean_folder}/{uuid.uuid4().hex}.{ext}"

    @staticmethod
    def _read_dimensions(uploaded_file) -> tuple[int | None, int | None, str]:
        try:
            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            width, height = image.size
            img_format = (image.format or "").lower()
        except Exception:  # noqa: BLE001 - dimensions are best-effort metadata
            width, height, img_format = None, None, ""
        finally:
            try:
                uploaded_file.seek(0)
            except Exception:  # noqa: BLE001 - unreadable file fails at save time
                pass
        return width, height, img_format
