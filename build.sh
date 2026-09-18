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

# Fail loudly instead of silently building with development settings.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
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
