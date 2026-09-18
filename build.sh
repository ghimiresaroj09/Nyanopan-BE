#!/usr/bin/env bash
#
# Render build script.
#
# Runs once per deploy, before the service starts:
#   1. installs Python dependencies
#   2. collects static files (admin/Swagger assets served by WhiteNoise)
#   3. applies database migrations
#
# Migrations live here because Render's `preDeployCommand` is only available on
# paid plans. On a paid plan you can move `migrate` into preDeployCommand and
# drop it from this script.

set -o errexit
set -o nounset
set -o pipefail

echo "==> Starting build process"
echo "==> Python version: $(python --version)"
echo "==> Current directory: $(pwd)"
echo "==> Virtual environment: ${VIRTUAL_ENV:-not set}"

# Fail loudly instead of silently building with development settings.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"
echo "==> DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

echo "==> Installing Python dependencies"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Verify Django is installed and settings are loadable
echo "==> Verifying Django installation"
python -c "import django; print(f'Django {django.get_version()} installed')"
python -c "import sys; print(f'Python executable: {sys.executable}')"
python -c "import os; print(f'DJANGO_SETTINGS_MODULE: {os.environ.get(\"DJANGO_SETTINGS_MODULE\", \"NOT SET\")}')"

echo "==> Testing Django setup"
python -c "import django; django.setup(); from django.conf import settings; print(f'Settings loaded: {settings.SETTINGS_MODULE}'); print(f'staticfiles in INSTALLED_APPS: {\"django.contrib.staticfiles\" in settings.INSTALLED_APPS}')"

echo "==> Available management commands:"
python manage.py help | head -20

echo "==> Running collectstatic"
# Collectstatic doesn't access the database, so we can use a dummy DATABASE_URL
# if the real one isn't set yet (e.g., on first deploy before environment is configured)
if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL not set, using dummy value for collectstatic"
  export DATABASE_URL="postgresql://dummy:dummy@localhost/dummy"
fi
python manage.py collectstatic --no-input --verbosity 2

echo "==> Running database migrations"
# Migrations run on the direct (non-pooled) endpoint when one is configured:
# Neon's PgBouncer runs in transaction mode and does not support session-level
# state that schema migrations can rely on. Plain Postgres (no pooler in front)
# simply needs DATABASE_URL, so the override only applies when it is set.
if [ -n "${DATABASE_URL_UNPOOLED:-}" ]; then
  echo "Running migrations on the direct (unpooled) Neon endpoint."
  DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py migrate --no-input
else
  python manage.py migrate --no-input
fi

echo "Build finished: dependencies installed, static files collected, migrations applied."
