# DirectAdmin deployment guide

This guide deploys the Django backend on Himalayan Host DirectAdmin with Python
3.13.18, Passenger (if enabled by the Python Application feature), and MySQL or
MariaDB. It does not run deployment commands automatically.

## Python 3.13.18 and dependency compatibility

`.python-version` remains `3.13`. `requirements.txt` now requires Django 5.2.8+
within the existing Django 5.x range; Django 5.2.8 is the first 5.2 release
that officially supports Python 3.13. Django REST Framework and the other
Django/Python-only packages use compatible universal wheels or pure Python
code; package version ranges are not a lockfile, so pip will resolve current
versions that satisfy those ranges at install time.

`mysqlclient` is constrained to 2.2.5+ because that release added Python 3.13
Windows wheels; Linux shared hosting generally builds its C extension from the
source distribution and still needs the native development files below. Pillow
10.x/11.x (the project's allowed range) has CPython 3.13 wheels for common
Linux x86-64/aarch64 glibc platforms. Gunicorn is pure Python and supports
Python 3.13, but may not be the server DirectAdmin uses for this application.
The project also lists `psycopg[binary]` for PostgreSQL development/configuration
and pytest packages for development; neither is needed to serve this MySQL
production application, but they remain in the shared requirements file.

The exact availability of compatible wheels depends on DirectAdmin's CPU
architecture and system glibc. This guide does not install packages on the
hosting account; verify using the DirectAdmin virtualenv during deployment.

## DirectAdmin Python Application settings

Create the application using the Python 3.13.18 interpreter. Use the repository
directory as the application root, outside the public document root when the
panel permits it. Set:

- **Application URL:** `api.nyanopan.com/` (root of the API subdomain)
- **Application startup file:** `passenger_wsgi.py`
- **Application entry point:** `application`
- **WSGI callable:** `config.wsgi:application`
- **Settings module environment value:** `config.settings.production`

The root `passenger_wsgi.py` sets production settings by default, then imports
the `application` callable from `config.wsgi`. If DirectAdmin asks for a module
instead of a startup file, use `config.wsgi` and callable `application`.

If the panel uses a different process manager instead of Passenger, use that
manager's documented WSGI setup with the same callable and settings value.

## Environment variables

Set these in the DirectAdmin application environment. Do not commit real values
to Git or put a secrets file in a web-accessible directory.

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<secure-random-secret>
DEBUG=False

DATABASE_URL=mysql://<DB_USER>:<URL_ENCODED_DB_PASSWORD>@localhost:3306/<DB_NAME>

ALLOWED_HOSTS=api.nyanopan.com
CORS_ALLOWED_ORIGINS=https://nyanopan.com,https://admin.nyanopan.com
CSRF_TRUSTED_ORIGINS=https://api.nyanopan.com,https://nyanopan.com,https://admin.nyanopan.com

# Set True after confirming that HTTPS works and Passenger/Apache reports HTTPS
# correctly to Django. Default is True in production settings.
SECURE_SSL_REDIRECT=True

# Keep HSTS disabled (0) until HTTPS and all relevant domain certificates are
# verified. Production settings default this to 0.
SECURE_HSTS_SECONDS=0

# Optional but recommended for persistent user uploads:
CLOUDINARY_CLOUD_NAME=<cloudinary-cloud-name>
CLOUDINARY_API_KEY=<cloudinary-api-key>
CLOUDINARY_API_SECRET=<cloudinary-api-secret>
CLOUDINARY_UPLOAD_FOLDER=ecommerce
# USE_CLOUDINARY=True

# Optional app features:
ADMIN_EMAIL=<initial-admin-email>
ADMIN_PASSWORD=<strong-initial-admin-password>
CRON_SECRET=<long-random-secret>

# Optional SMTP email configuration:
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-username>
EMAIL_HOST_PASSWORD=<smtp-password>
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=<sender-address>
```

`DATABASE_URL` is required by production settings and must use the MySQL scheme.
URL-encode reserved characters in the database username or password (for
example `@` as `%40`, `/` as `%2F`, and `#` as `%23`). Use the actual database
name and user as shown by DirectAdmin; some panels prefix them with the hosting
account name. The MySQL account must be granted privileges on that database.

`CLOUDINARY_*` values are optional. If all three Cloudinary credentials are
present, uploads use Cloudinary by default; set `USE_CLOUDINARY=True` to make
that explicit. Without Cloudinary, uploads use `MEDIA_ROOT` (`<app-root>/media`)
on local disk. That directory must be writable by the application user, backed
up, and served by Apache through an explicit media alias/location. Django does
not serve media in production. Local uploads can be lost if the application is
recreated or moved, so Cloudinary or another persistent object store is
recommended.

`ADMIN_EMAIL` and `ADMIN_PASSWORD` seed an admin user when the first migration
process runs. `CRON_SECRET` enables protected maintenance endpoints when set to
at least 16 characters. SMTP variables are only needed for email delivery.

## Install dependencies and collect static files

Open the DirectAdmin application terminal or SSH session. Activate the virtual
environment created for this Python application and change to the repository
root. Substitute the actual virtualenv and application paths shown by DirectAdmin:

```bash
source <DIRECTADMIN_VENV_PATH>/bin/activate
cd <APPLICATION_ROOT>
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py check --deploy --settings=config.settings.production
python manage.py collectstatic --noinput --settings=config.settings.production
```

The reported interpreter should be Python 3.13.18. Do not use the Render-only
`build.sh` on DirectAdmin; it assumes a Render build environment and its
migration logic is not suitable here.

### Verify Python 3.13.18 dependency installation

Run this in the DirectAdmin app's own virtualenv. `pip install` is the actual
compatibility check; a resolver dry run alone cannot detect native build or
import failures. It does not connect to the database or run migrations.

```bash
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
python -c "import django, rest_framework, MySQLdb, PIL, gunicorn, cloudinary, whitenoise; print('Django', django.get_version()); print('DRF', rest_framework.VERSION); print('Pillow', PIL.__version__); print('mysqlclient import OK')"
```

The version command must report `Python 3.13.18`. Save the full pip output if
installation fails; in particular, `mysqlclient` errors mentioning `pkg-config`,
`mysql.h`, a compiler, or linker libraries indicate missing host build
dependencies. A successful installation plus `pip check` and imports verifies
the resolved dependency set in that virtualenv, not every possible future
resolution allowed by the unpinned version ranges.

### Verify the actual database schema (read only)

Run these read-only queries in DirectAdmin's database management UI, selecting
the production database first. They do not alter schema or migration history:

```sql
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE,
       COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'cms_blog'
  AND COLUMN_NAME = 'meta_robots';

SELECT app, name, applied
FROM django_migrations
WHERE app = 'cms'
  AND name IN (
    '0015_blog_seo_fields',
    '0016_blog_og_url_robots_options',
    '0017_blog_image_metadata',
    '0018_blog_image_url_capacity',
    '0019_widen_blog_robots_column'
  )
ORDER BY applied;
```

Expected column result: `COLUMN_TYPE` is `varchar(64)` and `IS_NULLABLE` is
`NO`. Migration history should show a contiguous applied sequence through the
current migration level. If `0019` is absent, it is an empty migration now and
may be applied normally after reviewing the pending plan. If history includes
`0016` but the column is not `varchar(64)`, stop: the database has schema drift
that needs a separate repair plan. Do not manually edit `django_migrations` or
fake migrations to hide that mismatch.

The repository's migration loader can also verify the source migration state
without connecting to the database:

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python - <<'PY'
import django
django.setup()
from django.db.migrations.loader import MigrationLoader

loader = MigrationLoader(None, ignore_no_migrations=True)
for target in (
    ("cms", "0018_blog_image_url_capacity"),
    ("cms", "0019_widen_blog_robots_column"),
):
    field = loader.project_state(target).apps.get_model("cms", "Blog")._meta.get_field("meta_robots")
    print(target[1], "max_length=", field.max_length)
PY
```

### Native package build requirements

`mysqlclient` is constrained to version 2.2.x by `requirements.txt`. On Linux
it commonly installs from source and needs a C compiler, Python development
headers, `pkg-config`, and MySQL/MariaDB Connector/C development headers and
libraries. Ask the host to provide these if pip reports a `pkg-config` or
`mysql.h` error. Pillow has CPython 3.13 Linux wheels for common glibc x86-64
and aarch64 platforms; an unsupported CPU architecture or older system library
may force a source build requiring image libraries and build tools.

Gunicorn is listed for process serving but DirectAdmin may use Passenger to
host the Python application. Use the panel's selected process manager; Gunicorn
does not replace the configured Passenger WSGI entry point.

## MySQL migration compatibility check

Migration `apps/cms/migrations/0019_widen_blog_robots_column.py` previously
contained `ALTER TABLE cms_blog ALTER COLUMN meta_robots TYPE varchar(64)`,
which is PostgreSQL syntax and invalid on MySQL/MariaDB. That SQL was redundant:
migration `0015` already adds `meta_robots` with length 64, and `0016` alters
the field to length 64 again. Migrations `0017` and `0018` do not change it.
Migration `0019` is now an empty migration node, preserving its identity and
dependency graph while allowing fresh MySQL/MariaDB installations to proceed.
Existing PostgreSQL databases that recorded `0019` keep their migration
history; those that have not recorded it will apply it as a no-op.

The repository does not contain the production `django_migrations` table, and
production was not queried. Before deployment, compare the recorded CMS
migrations and actual `cms_blog.meta_robots` column definition on the target
database. If the physical column is shorter than 64 despite migration history
through `0016`, treat that as schema drift and plan a separately reviewed,
database-aware repair; this empty migration intentionally does not rewrite
columns that the migration state already declares correct. Do not fake a
migration or manually mark it applied without checking the live schema.

## Migration and restart steps

First confirm the MySQL URL is set in the application environment, then review
the pending plan:

```bash
python manage.py migrate --plan --settings=config.settings.production
```

After reviewing the plan, take a database backup and apply migrations manually:

```bash
python manage.py migrate --noinput --settings=config.settings.production
```

Do not run migrations from a Git build hook or against production until the
plan and backup have been reviewed. After code, environment, static files, or
migrations are updated, use DirectAdmin's **Restart** or **Reload** action for
the Python application. If that control is unavailable, use the Passenger
restart mechanism documented by DirectAdmin/host support for this account.

## Static files and media

The project sets `STATIC_ROOT` to `<application-root>/staticfiles` and uses
WhiteNoise's compressed manifest storage in production. Run `collectstatic`
after dependency or static asset changes. Ensure the directory is writable by
the app during collection. WhiteNoise middleware serves the collected static
files through the Django app; verify the DirectAdmin/Apache configuration does
not intercept `/static/` incorrectly.

The media directory is separate from static files. Production URLs under
`/media/` are not served by Django. Configure an Apache alias for the persistent
media directory if using local uploads, or use Cloudinary for durable hosted
media.

## Troubleshooting

- **`mysqlclient` build fails:** ask the host to enable compiler tools, Python
  3.13 headers, `pkg-config`, and MySQL/MariaDB Connector/C development headers.
- **`No module named MySQLdb`:** install `requirements.txt` with the same Python
  3.13 virtualenv selected by the DirectAdmin app.
- **SQLite or PostgreSQL engine error:** production requires a MySQL-scheme
  `DATABASE_URL`; verify that the app environment has the correct value.
- **Database access denied / connection refused:** verify the database host,
  prefixed DB name/user, password encoding, user grants, and localhost policy.
- **`DisallowedHost`:** set `ALLOWED_HOSTS=api.nyanopan.com` in the app environment.
- **Browser CORS error:** include the exact frontend origins in
  `CORS_ALLOWED_ORIGINS` (scheme included, no path or trailing slash).
- **Admin CSRF 403:** include `https://api.nyanopan.com` in
  `CSRF_TRUSTED_ORIGINS` and verify the external HTTPS host/proxy settings.
- **Static 404 or manifest error:** rerun `collectstatic`, ensure the static
  directory is writable, and inspect Apache handling of `/static/`.
- **Uploads fail or disappear:** check media directory permissions and Apache
  media mapping, or configure all Cloudinary credentials.
- **Passenger import error:** verify app root, Python version/virtualenv,
  startup file `passenger_wsgi.py`, and callable `application`; then restart.
- **HTTPS redirect loop:** ask the host whether Passenger/Apache provides
  `HTTPS` or `X-Forwarded-Proto` correctly before enabling redirect behavior.
