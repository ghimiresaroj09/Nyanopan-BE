"""Development settings: debug on, sqlite default, permissive CORS."""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS + ["localhost", "127.0.0.1", "[::1]"]))

# Frontend dev servers run on various ports; allow all origins locally.
CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
