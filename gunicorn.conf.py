"""Gunicorn configuration for production (Render).

Render passes the port to bind via ``$PORT`` (10000 by default) and captures
stdout/stderr into the service log stream, so both access and error logs are
written to ``-`` (stdout).

Tunables (all optional, read from the environment):

    PORT                   bind port, default 10000
    WEB_CONCURRENCY        worker processes, default min(4, 2 * CPUs + 1)
    GUNICORN_THREADS       threads per worker, default 4
    GUNICORN_TIMEOUT       request timeout in seconds, default 120
    GUNICORN_LOG_LEVEL     debug|info|warning|error, default info
"""

import multiprocessing
import os


def _int_env(name: str, default: int) -> int:
    try:
        return int((os.environ.get(name) or "").strip() or default)
    except ValueError:
        return default


bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Sync workers with threads keep memory low while still handling the
# occasional slow image upload to Cloudinary.
worker_class = "gthread"
workers = _int_env("WEB_CONCURRENCY", min(4, multiprocessing.cpu_count() * 2 + 1))
threads = _int_env("GUNICORN_THREADS", 4)

# Image uploads (up to MAX_IMAGE_UPLOAD_MB) can take a while on a cold instance.
timeout = _int_env("GUNICORN_TIMEOUT", 120)
graceful_timeout = _int_env("GUNICORN_GRACEFUL_TIMEOUT", 30)
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = (os.environ.get("GUNICORN_LOG_LEVEL") or "info").lower()
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s bytes %(M)sms'
