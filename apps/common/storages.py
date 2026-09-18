"""Image storage backend: Cloudinary with a local filesystem fallback.

Uploads go to Cloudinary when ``USE_CLOUDINARY`` is true (auto-enabled when all
three ``CLOUDINARY_*`` credentials are set); otherwise files are stored under
``MEDIA_ROOT`` so local development and the test suite need no account.

``image_storage`` is a callable (not an instance) so the choice is evaluated at
runtime — and so model fields could reference it without migrations changing
when the backend toggles.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, Storage

try:
    from cloudinary_storage.storage import MediaCloudinaryStorage
except ImportError:  # pragma: no cover - package is in requirements.txt
    MediaCloudinaryStorage = None  # type: ignore[assignment]


def _cloudinary_enabled() -> bool:
    return bool(getattr(settings, "USE_CLOUDINARY", False))


def image_storage() -> Storage:
    """Storage for catalog images (Cloudinary ``resource_type=image`` or local)."""
    if _cloudinary_enabled():
        if MediaCloudinaryStorage is None:
            raise ImproperlyConfigured(
                "USE_CLOUDINARY is True but 'django-cloudinary-storage' is not installed."
            )
        return MediaCloudinaryStorage()
    return FileSystemStorage()
