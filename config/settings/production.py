"""Production settings: hardened defaults, PostgreSQL expected.

Targets Render (https://render.com): reads configuration from environment
variables, trusts the platform's TLS-terminating proxy, serves static files
through WhiteNoise, and logs to stdout so the platform log stream catches
everything.
"""

import os
import sys
import warnings

from django.core.exceptions import ImproperlyConfigured

try:
    from .base import *  # noqa: F401,F403
except Exception as e:
    sys.stderr.write(f"ERROR loading base settings: {e}\n")
    sys.stderr.write(f"Python path: {sys.path}\n")
    sys.stderr.write(f"Current directory: {os.getcwd()}\n")
    raise

# ---------------------------------------------------------------------------
# Core guards — fail at import time rather than serving a broken deployment
# ---------------------------------------------------------------------------
DEBUG = False

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured("A strong SECRET_KEY environment variable is required.")

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    raise ImproperlyConfigured("PostgreSQL (DATABASE_URL) is required in production.")

# Reuse connections between requests, but verify them first: Neon suspends idle
# computes and closes pooled connections, so a stale handle would otherwise
# raise on the first query after a pause. (dj_database_url already returns
# CONN_HEALTH_CHECKS=False, so set these explicitly rather than with setdefault.)
DATABASES["default"]["CONN_MAX_AGE"] = env_int("CONN_MAX_AGE", 600)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = env_bool("CONN_HEALTH_CHECKS", True)


# ---------------------------------------------------------------------------
# Hosts and CSRF trust
# ---------------------------------------------------------------------------
# Render injects RENDER_EXTERNAL_HOSTNAME (e.g. my-api.onrender.com) and uses
# that host — or a verified custom domain — as the Host header for its health
# checks, so it must always be allowed.
RENDER_EXTERNAL_HOSTNAME = (env("RENDER_EXTERNAL_HOSTNAME") or "").strip()
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RENDER_EXTERNAL_HOSTNAME]

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must list at least one hostname.")

# Custom domains need listing here *and* in ALLOWED_HOSTS (with scheme) or the
# session-based admin login is rejected by Django's CSRF protection.
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if RENDER_EXTERNAL_HOSTNAME:
    _render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, _render_origin]


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Render terminates TLS at its proxy and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Overridable for setups that must embed the API docs in a frame.
X_FRAME_OPTIONS = env("X_FRAME_OPTIONS", "DENY")


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
# Static files: WhiteNoise compresses them at build time and serves them with
# far-future caching headers from the manifest. The `default` (media) backend is
# inherited from base.py so it stays Cloudinary-aware — hardcoding a filesystem
# backend here would silently send future FileFields to the instance's
# ephemeral disk, which is wiped on every deploy.
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}


# ---------------------------------------------------------------------------
# Logging — everything to stdout, which Render captures
# ---------------------------------------------------------------------------
LOG_LEVEL = (env("LOG_LEVEL", "INFO") or "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # gunicorn installs its own handlers; keep them off the root logger.
        "gunicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# ---------------------------------------------------------------------------
# Deployment warnings
# ---------------------------------------------------------------------------
if not USE_CLOUDINARY:
    warnings.warn(
        "USE_CLOUDINARY is off. Uploaded images will be written to the local "
        "filesystem, which is wiped on every deploy on most platforms (Render "
        "included). Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and "
        "CLOUDINARY_API_SECRET for persistent media.",
        RuntimeWarning,
        stacklevel=2,
    )
