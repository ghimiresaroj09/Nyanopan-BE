"""Test settings: in-memory sqlite, fast hashing, filesystem image uploads."""

import cloudinary

from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

TESTING = True

# Never touch a real Cloudinary account from the test suite, even when the
# developer's .env has live credentials. Uploads go to the filesystem instead.
USE_CLOUDINARY = False
MEDIA_ROOT = BASE_DIR / "test_media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Dummy values so Cloudinary config/builders stay import-safe offline.
CLOUDINARY_CLOUD_NAME = "test-shop"
CLOUDINARY_API_KEY = "test-key"
CLOUDINARY_API_SECRET = "test-secret"
CLOUDINARY_UPLOAD_FOLDER = "test"
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
    "SECURE": True,
    "PREFIX": "",
    "MEDIA_TAG": "ecommerce-test",
}

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)
