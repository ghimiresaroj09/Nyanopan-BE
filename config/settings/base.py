"""Base settings shared by all environments.

Secrets and environment-specific values are read from environment variables
(populated from a local ``.env`` file during development). Nothing sensitive
is hardcoded here.
"""

import os
from datetime import timedelta
from pathlib import Path

import cloudinary
import dj_database_url
from dotenv import load_dotenv

try:
    import cloudinary_storage  # noqa: F401
except ImportError:
    # Cloudinary backend unavailable: image uploads fall back to MEDIA_ROOT and
    # USE_CLOUDINARY uploads fail with a clear error (see apps.common.storages).
    _CLOUDINARY_APPS: list[str] = []
else:
    _CLOUDINARY_APPS = ["cloudinary_storage", "cloudinary"]

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: str = "") -> list[str]:
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_int(key: str, default: int) -> int:
    try:
        return int((os.environ.get(key) or "").strip() or default)
    except ValueError:
        return default


SECRET_KEY = env("SECRET_KEY", "django-insecure-dev-placeholder-change-me")

DEBUG = False

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # django.contrib.staticfiles MUST come before *_CLOUDINARY_APPS.
    # Django resolves duplicate management commands in favour of the app listed
    # first, and django-cloudinary-storage ships its own `collectstatic` whose
    # copy_file() is a no-op unless static files live on Cloudinary. Listed after
    # this app, it shadows Django's command: nothing is copied into STATIC_ROOT
    # and WhiteNoise's manifest post-processing then fails with
    # "MissingFileError: admin/img/sorting-icons.svg" on a fresh checkout.
    "django.contrib.staticfiles",
    *_CLOUDINARY_APPS,
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    # Local
    "apps.common",
    "apps.accounts",
    "apps.catalog",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Database (PostgreSQL in production via DATABASE_URL, sqlite fallback locally)
# ---------------------------------------------------------------------------
_DATABASE_URL = (env("DATABASE_URL") or "").strip()
if _DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(_DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # The shop is public; admin endpoints opt in to IsAdminUser explicitly.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ---------------------------------------------------------------------------
# API documentation (drf-spectacular)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Ecommerce Shop API",
    "DESCRIPTION": (
        "Public catalog APIs and admin management APIs for a WhatsApp-checkout "
        "ecommerce shop. There is no customer authentication: shoppers browse "
        "the public catalog and check out via WhatsApp on the frontend. "
        "Admin product creation is a 3-step flow: Product 1/3 adds the "
        "product info, Product 2/3 adds the attributes, values and prices, "
        "and Product 3/3 adds the images."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "POSTPROCESSING_HOOKS": ["apps.common.spectacular.envelope_postprocessing_hook"],
    "COMPONENT_SPLIT_REQUEST": True,
    # Only JWT is documented: session auth stays enabled at runtime (browsable
    # API + Django admin) but is hidden from the schema, so `jwtAuth`
    # (http, Bearer) is the single offered scheme.
    "AUTHENTICATION_WHITELIST": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "TAGS": [
        {"name": "Public - Categories"},
        {"name": "Public - Products"},
        {"name": "Public - Product Models"},
        {"name": "Public - Attributes"},
        {"name": "Admin - Auth"},
        {
            "name": "Product 1/3 - Info",
            "description": (
                "Step 1 of the product flow: create the product with its "
                "basic info (name, category, model, description). The "
                "returned product id feeds steps 2 and 3."
            ),
        },
        {
            "name": "Product 2/3 - Attributes, Values & Price",
            "description": (
                "Step 2 of the product flow: attach the attribute palette "
                "to the product and set each variant's price."
            ),
        },
        {
            "name": "Product 3/3 - Images",
            "description": (
                "Step 3 of the product flow: upload each value's featured "
                "image and gallery images."
            ),
        },
        {"name": "Admin - Categories"},
        {"name": "Admin - Product Models"},
        {"name": "Admin - Attributes"},
        {"name": "Admin - Attribute Values"},
        {"name": "Admin - Product Attribute Values"},
        {"name": "Admin - Variants"},
        {"name": "Admin - Variant Options"},
        {"name": "Admin - Images"},
        {
            "name": "Internal",
            "description": (
                "Token-guarded endpoints called by the external scheduler "
                "(cron-job.org) to run maintenance jobs. They take the shared "
                "secret in the X-Cron-Secret header, not a bearer token."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOW_ALL_ORIGINS = False


# ---------------------------------------------------------------------------
# Image storage: Cloudinary with a local filesystem fallback.
# Only URLs/public_ids live in the database, never binary data.
# ---------------------------------------------------------------------------
CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET", "")
CLOUDINARY_UPLOAD_FOLDER = env("CLOUDINARY_UPLOAD_FOLDER", "ecommerce")

USE_CLOUDINARY = env_bool(
    "USE_CLOUDINARY",
    bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET),
)

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
    "SECURE": True,
    # No global PREFIX: the image service composes "folder/filename" names
    # itself so the upload endpoint keeps its custom-folder parameter.
    "PREFIX": "",
    "MEDIA_TAG": "ecommerce",
}

# Upload limits (enforced by apps.common.validators).
MAX_IMAGE_UPLOAD_MB = env_int("MAX_IMAGE_UPLOAD_MB", 5)

STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if (USE_CLOUDINARY and _CLOUDINARY_APPS)
            else "django.core.files.storage.FileSystemStorage"
        )
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

# Legacy alias: django-cloudinary-storage's collectstatic override still reads
# STATICFILES_STORAGE on Django 5+. Mirrors STORAGES["staticfiles"]["BACKEND"].
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME or None,
    api_key=CLOUDINARY_API_KEY or None,
    api_secret=CLOUDINARY_API_SECRET or None,
    secure=True,
)


# ---------------------------------------------------------------------------
# Seeded admin (auto-created after `migrate` when email+password are set)
# ---------------------------------------------------------------------------
ADMIN_SEED_EMAIL = env("ADMIN_EMAIL", "")
ADMIN_SEED_PASSWORD = env("ADMIN_PASSWORD", "")


# ---------------------------------------------------------------------------
# Internal cron endpoints (called by the external scheduler, see
# apps.common.cron). Empty/short values disable them: they answer 503.
# ---------------------------------------------------------------------------
CRON_SECRET = env("CRON_SECRET", "")

TESTING = False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
