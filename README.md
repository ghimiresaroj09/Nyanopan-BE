# Ecommerce Shop — Backend

Django + Django REST Framework backend for a modern ecommerce/shop website with a
**public catalog** and a **WhatsApp-based checkout on the frontend**.

The backend provides catalog data and admin management only. It intentionally does
**not** implement customer authentication, carts, checkout, orders, payments,
inventory, or WhatsApp messaging — the frontend owns the entire shopping
experience and redirects the shopper to WhatsApp with the selected variants.

## Technology stack

| Layer | Choice |
|---|---|
| Language | Python 3.10+ |
| Framework | Django 5.2 (LTS), Django REST Framework |
| Database | PostgreSQL (production) / SQLite (local default) |
| Image storage | Cloudinary via `django-cloudinary-storage` (filesystem fallback when unconfigured) |
| Admin auth | JWT (`djangorestframework-simplejwt`, staff users only) |
| Filtering | `django-filter` |
| API docs | OpenAPI via `drf-spectacular` (Swagger + ReDoc) |
| Config | Environment variables (`python-dotenv`) |
| Testing | `pytest` + `pytest-django` |
| IDs | UUID primary keys on every model |
| SKUs | Auto-generated from product + options when blank (override allowed) |
| Prod serving | `gunicorn` + `whitenoise` |

## Architecture

```text
ecommerce/
├── config/
│   ├── settings/
│   │   ├── base.py          # shared settings (env-driven)
│   │   ├── development.py   # local development
│   │   ├── production.py    # hardened production
│   │   └── test.py          # pytest settings
│   ├── urls.py              # /admin, /api/docs, /api/v1/...
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/            # admin-only JWT auth (login/refresh/logout/me/change-password)
│   ├── catalog/             # categories, products, attributes, variants
│   │   ├── models.py        # relationships + model-level validation + DB constraints
│   │   ├── selectors.py     # optimized read queries (select/prefetch, no N+1)
│   │   ├── filters.py       # django-filter filtersets + price ordering filter
│   │   ├── services/        # business logic (products, variants, categories, images)
│   │   ├── serializers/     # public/ (read) + admin/ (write) representations
│   │   ├── views/           # public/ (read-only) + admin/ (staff-only) endpoints
│   │   ├── admin.py         # Django admin screens + inlines
│   │   └── management/      # seed_initial_data command
│   └── common/              # timestamps, pagination, permissions, error envelope, utils
├── manage.py
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

**Layering rules**

- Views are thin: they pick serializers/querysets and delegate writes to services.
- Serializers validate API input and shape representations.
- Services (`apps/catalog/services/`) own multi-model business logic and run inside
  `transaction.atomic()` blocks.
- Models own relationships, DB constraints, and model-level invariants (`clean()`).
- Read queries live in `selectors.py` with `select_related`/`prefetch_related`.

### Data model

```text
Category ──< Product >── ProductModel        (PROTECT on both FKs)
                │
                ├── gender (MEN/WOMEN/UNISEX/KIDS/BABY)
                ├── key_features (JSON: [{title, value}, ...])
                │
                ├────< ProductAttributeValue >── Attribute (requires_image?)
                │         │                      AttributeValue (unique per attribute)
                │         ├── feature_image (ImageField on shared storage + title/caption/alt)
                │         └── additional_images >── ProductAttributeImage (ImageField rows)
                │
                └────< ProductVariant (Decimal price, unique sku, optional name)
                            │── sku (unique), name, is_special_edition, is_active
                            └────< ProductVariantOption (through model)
                                        └── ProductAttributeValue (same product only)
```

Key invariants (enforced at model + serializer + service level, backed by DB
constraints where possible):

- `AttributeValue` must belong to the chosen `Attribute`.
- Attributes with `requires_image=True` (e.g. **Color**) force every *active*
  product value to carry a feature image. New image-requiring attributes need no
  code changes — just flip the flag.
- A variant option must belong to the variant's product; one value per attribute.
- No two variants of a product may share the same option combination (checked in
  a locked transaction).
- Variants need ≥ 1 option; prices are `Decimal` (never float); no inventory.
- Variant SKUs auto-generate at creation when blank and stay stable afterwards; slugs follow renames unless explicitly set.

## Environment variables

Copy `.env.example` to `.env` and fill it in:

```text
SECRET_KEY=
DEBUG=
DATABASE_URL=

CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_UPLOAD_FOLDER=ecommerce
# USE_CLOUDINARY=True        # force on/off (default: on when all 3 creds set)
# MAX_IMAGE_UPLOAD_MB=5      # per-image upload limit

ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key (required, strong value in production) |
| `DATABASE_URL` | e.g. `postgres://user:pass@localhost:5432/shopdb` (defaults to local `db.sqlite3`) |
| `CLOUDINARY_*` | Cloudinary credentials + upload folder for all catalog images |
| `USE_CLOUDINARY` | Force Cloudinary on/off (default: on when all 3 creds set; off = local `media/`) |
| `MAX_IMAGE_UPLOAD_MB` | Per-image upload limit in MB (default `5`) |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins (dev allows all) |
| `ADMIN_EMAIL` | Seeded superuser login email (auto-created after `migrate`) |
| `ADMIN_PASSWORD` | Password for the seeded superuser (never commit real values) |

## Media storage (Cloudinary)

Catalog images upload through `POST /api/v1/admin/images/upload/` as
`multipart/form-data` with an `image` file field (`string($binary)` in the API
docs) plus an optional `folder`. The response carries the `url` + `public_id`
to reference inside category / product-attribute payloads; `POST
/api/v1/admin/images/delete/` removes an asset by `public_id`.

Every catalog image is an `ImageField` on the shared Cloudinary/filesystem
storage: the database keeps the asset name and `.url` builds the delivery
URL (Cloudinary `secure_url`, or an absolute `/media/` URL in local mode).

- Cloudinary is used when `USE_CLOUDINARY` is true (the default when all three
  `CLOUDINARY_*` credentials are set); otherwise files are stored under local
  `media/` and served from `/media/` in development. The test suite always uses
  the filesystem, so it needs no credentials or network access.
- Uploads are validated with Pillow plus an extension allowlist
  (`jpg/jpeg/png/webp/gif`) and a size cap (`MAX_IMAGE_UPLOAD_MB`, default 5).
- Deleting or replacing a record's images schedules the old assets for cleanup
  after the database transaction commits, so failed writes never lose images
  and successful writes leave no orphans.

```bash
curl -X POST http://localhost:8000/api/v1/admin/images/upload/ \
  -H "Authorization: Bearer $ACCESS" \
  -F image=@photo.png -F folder=products
```

Image fields on categories and product values accept files two ways: send
`multipart/form-data` with binary files (`image`, `feature_image`, and repeat
`additional_images` for multiple), or `application/json` referencing an existing
asset with a `{url}` / `{name}` / `{public_id}` object (round-trip what a prior
read returned). Inside nested product payloads,
images reference file parts instead: `attribute_values`/`variants`/
`key_features` go in as JSON-encoded strings and image slots use
`{"file": "<part-name>"}`:

```bash
curl -X POST http://localhost:8000/api/v1/admin/products/ \
  -H "Authorization: Bearer $ACCESS" \
  -F name="Wool Slippers" -F model="<uuid>" -F gender="UNISEX" -F category="<uuid>" \
  -F attribute_values='[{"key": "grey", "attribute": "<uuid>", "attribute_value": "<uuid>", "feature_image": {"file": "grey-img"}}]' \
  -F variants='[{"price": "5995.00", "options": [{"key": "grey"}]}]' \
  -F grey-img=@grey.png
```

Simplest for JSON clients: image slots also accept an inline base64 upload —
`{"file": "data:image/png;base64,..."}` (png/jpg/webp/gif, same
`MAX_IMAGE_UPLOAD_MB` limit) — so a product with images can be created in a
single JSON request with no pre-upload and no multipart parts.

## Installation

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then edit .env
```

### PostgreSQL setup

```bash
createdb shopdb
createuser shop_user -P          # set a strong password
# .env:
# DATABASE_URL=postgres://shop_user:<password>@localhost:5432/shopdb
```

(For a quick start you can skip PostgreSQL — SQLite is used when `DATABASE_URL`
is empty. Production **requires** PostgreSQL.)

### Cloudinary setup

1. Create a (free) account at https://cloudinary.com and open the dashboard.
2. Copy **Cloud name**, **API key**, **API secret** into `.env`
   (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`).
3. Uploads go to `CLOUDINARY_UPLOAD_FOLDER` (default `ecommerce`).

Admin image flow: `POST /api/v1/admin/images/upload/` a file → paste the returned
`{url, public_id, ...}` reference into category / product-attribute payloads.
Replaced or deleted images are removed from Cloudinary automatically **after** the
database transaction commits, so failed writes never lose images and successful
writes leave no orphans.

### Migrations, superuser, seed data

```bash
python manage.py migrate            # also auto-seeds the ADMIN_* superuser when configured
python manage.py createsuperuser    # optional extra admins
python manage.py seed_initial_data  # Color(requires image)/Size/Material attributes
```

Set `ADMIN_EMAIL`/`ADMIN_PASSWORD` in `.env` and every `migrate`
ensures that superuser exists (idempotent — an existing password is never reset).

### Running the development server

```bash
python manage.py runserver
```

- API: http://127.0.0.1:8000/api/v1/
- Docs: http://127.0.0.1:8000/api/docs/ (Swagger), `/api/redoc/`, `/api/schema/`
- Django admin: http://127.0.0.1:8000/admin/

### Running tests

```bash
pytest
```

217 tests covering models, services, public/admin APIs, permissions, validation
envelopes, image cleanup, and N+1 query bounds. Tests use in-memory SQLite and
mocked Cloudinary — no network or credentials needed.

## API overview

All endpoints are versioned under `/api/v1/`.

### Public (no auth, active records only)

```text
GET /api/v1/categories/                  # list (slug, image object, product_count)
GET /api/v1/categories/{slug}/

GET /api/v1/products/                    # list cards: price_range, primary_image
GET /api/v1/products/{slug}/             # full page: attributes, images, variants

GET /api/v1/product-models/
GET /api/v1/product-models/{slug}/

GET /api/v1/attributes/
GET /api/v1/attributes/{id}/
```

Product list supports pagination (`page`, `page_size`), search (`?search=`),
filters (`?category=slippers&gender=UNISEX&is_featured=true&min_price=&max_price=`)
and sorting (`?ordering=price|-price|-created_at|name`).

The detail response groups attribute values (with color images) and lists every
variant with its price/special-edition flag plus
`product_attribute_value` ids per option — the frontend matches the shopper's
selection against these ids to find the SKU, then checks out via WhatsApp.

### Admin auth (staff users only, JWT)

```text
POST /api/v1/admin/auth/login/           # {email, password} -> {access, refresh, user}
POST /api/v1/admin/auth/refresh/         # {refresh} -> {access}
POST /api/v1/admin/auth/logout/          # {refresh} (blacklisted)
POST /api/v1/admin/auth/change-password/ # {old_password, new_password}
GET  /api/v1/admin/auth/me/
```

Send `Authorization: Bearer <access>` on admin requests.

### Admin catalog CRUD (staff only)

```text
/api/v1/admin/categories/
/api/v1/admin/product-models/
/api/v1/admin/products/              # supports nested attribute_values + variants
/api/v1/admin/attributes/
/api/v1/admin/attribute-values/  # single {attribute, name} or bulk {attribute, value: [...]}
/api/v1/admin/attribute-values/bulk/  # bulk-only alias of the above
/api/v1/admin/product-attribute-values/
/api/v1/admin/variants/
/api/v1/admin/variant-options/
/api/v1/admin/images/upload/         # multipart file -> {public_id, url, ...}
/api/v1/admin/images/delete/         # {public_id} -> {deleted}
```

Standard `GET/POST/PATCH/DELETE`. Nested product creation accepts temporary
`key` references so variants can point at values created in the same request;
the whole write is atomic. Partial updates never delete omitted relations.

Writes accept UUIDs or human keys anywhere a reference appears: category /
model / product slugs (`"slippers"`), attribute names (`"Color"`), value names
resolved within the attribute (`"Grey"`), and variant
SKUs. Matching is exact-first with a single-match case-insensitive fallback.
Attributes also accept nested `"value": [...]` names on create (all-or-nothing)
and update (missing names are added, existing ones are left untouched).

Category/product image payload shape:

```json
{ "url": "https://res.cloudinary.com/...", "public_id": "ecommerce/abc",
  "title": "...", "caption": "...", "alt": "..." }
```

(`null` clears, a plain URL string sets just the URL.)

### Product variant values (tab 2, staff only)

```text
POST  /api/v1/productvarientvalues/{product_id}/
PATCH /api/v1/productvarientvalues/{product_id}/
```

`POST` accepts the frontend's attribute palette plus its generated
combinations (`{attributes, generatedVarients}`) and upserts every variant
by SKU within the product (same SKU updates price/name/flags/options, new
SKU creates). Responds `201` with the status envelope and message
`ProductVarientValue created successfully`. `PATCH` is the slim bulk
update: `{generatedVarients: [{sku, price?, name?, is_active?,
is_special_edition?}]}` changes only the sent fields (options stay as-is),
responds `200` with `ProductVarientValues updated successfully`, and fails
the whole request atomically on any unknown SKU — nothing is created.
Variant prices are plain numbers with no currency object — the frontend
shows a static symbol. The same URL without the trailing slash works too.

### Product variant images (tab 3, staff only)

```text
GET  /api/v1/productvarientimages/{product_id}/
POST /api/v1/productvarientimages/{product_id}/
DELETE /api/v1/productvarientimages/{product_id}/images/{image_id}/
```

`GET` lists the values *used on* the product, grouped by attribute with
their current featured and gallery images. `POST {"value", feature_image?,
additional_images?}` uploads onto one value: featured is replaced (`null`
clears it), gallery images are appended. Accepts JSON (base64 data-URI
`{"file": ...}` / `{"url": ...}` slots) or multipart (binary `feature_image`
part, repeated `additional_images` parts). `DELETE` removes one gallery
image. Images live on the value, so every variant sharing it (Red S, Red M,
...) resolves the same pictures automatically. Status envelope with
`ProductVarientImages retrieved successfully` /
`ProductVarientImage uploaded successfully` /
`ProductVarientImage deleted successfully`. Bare (slashless) URLs work too.

### Response format

Every API id is a UUID string. Success responses use one of two envelopes:

- **Product endpoints** (`/api/v1/admin/products/...`) return the status
  envelope, where `statusCode` always mirrors the HTTP status:

```json
{ "status": "success", "message": "Products retrieved successfully.", "statusCode": 200, "data": { "...": "..." } }
```

  Product messages are `Products retrieved successfully.` (list),
  `Product retrieved successfully.` (detail), `Product created successfully.`,
  `Product updated successfully.`, and `Product deleted successfully.` (with
  `"data": {}`). Product `data` is a lean shape — scalar fields plus nested
  `model`/`category` objects (`{id, name, slug, description, isActive}`); it
  never embeds attribute values or variants. Nested `attribute_values` /
  `variants` are still accepted on write and can be managed afterwards via
  their own endpoints.

- **All other endpoints** return the legacy envelope:

```json
{ "success": true, "message": "...", "data": { "...": "..." } }
```

Errors everywhere share one envelope and carry `errors` instead of `data`:

```json
{ "success": false, "message": "Validation failed.", "errors": { "gender": ["..."] } }
```

List endpoints keep the pagination object inside `data`:

```json
{
  "status": "success",
  "message": "Products retrieved successfully.",
  "statusCode": 200,
  "data": { "count": 1, "next": null, "previous": null, "results": [{ "...": "..." }] }
}
```

Successful product `DELETE` requests return `200` with
`{"status": "success", "message": "Product deleted successfully.", "statusCode": 200, "data": {}}`;
other endpoints return the legacy `{"success": true, "message": "Deleted successfully.", "data": {}}`.

## Deploying to Render

The repository ships Render-ready files — no dashboard fiddling beyond
pasting a few secrets:

| File | Purpose |
| --- | --- |
| `render.yaml` | Blueprint: web service, env wiring, health check |
| `build.sh` | Build command: install deps → `collectstatic` → `migrate` |
| `gunicorn.conf.py` | Binds `$PORT`, gthread workers, access/error logs to stdout |
| `.python-version` | Pins Python 3.13 (Render's default is 3.14) |
| `/api/health/live/` | Process-only liveness probe (`healthCheckPath`), no database |
| `/api/health/` | Readiness probe (database included), `200` / `503` |
| `/api/v1/internal/cron/` | Token-guarded maintenance jobs for the external scheduler |

### Database (Neon)

Postgres is hosted on [Neon](https://neon.com) (project region
`ap-southeast-1` / Singapore — the same region the Render service runs in).
Neon gives the same database **two endpoints**, and the app uses both:

| Variable | Endpoint | Used for |
| --- | --- | --- |
| `DATABASE_URL` | pooled — host contains `-pooler` | all application traffic |
| `DATABASE_URL_UNPOOLED` | direct — no `-pooler` | `migrate` inside `build.sh` |

Migrations use the direct endpoint because Neon's PgBouncer runs in
*transaction* mode, where session-level state isn't supported (Neon's own
guidance is to run schema migrations over a direct connection). Runtime
traffic stays pooled. `build.sh` falls back to `DATABASE_URL` when no
unpooled URL is set, so plain Postgres still works.

Both URLs need `?sslmode=require`. Django issues no session-level `SET`
statements (the server's timezone is already UTC), so the pooled endpoint is
safe for normal request traffic.

### Deploy

1. Push this repo to GitHub.
2. Render Dashboard → **New +** → **Blueprint** → pick the repo → **Apply**.
   Render creates the `ecommerce-api` web service in `singapore`, generates
   `SECRET_KEY`, and prompts for the rest. No database is provisioned by
   Render — Neon is external.
3. Paste the two Neon connection strings plus the other prompted variables
   (fields marked `sync: false` are never stored in git):
   `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `CLOUDINARY_CLOUD_NAME`,
   `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `ADMIN_EMAIL`,
   `ADMIN_PASSWORD`, `CORS_ALLOWED_ORIGINS`.
4. The first deploy runs `build.sh`: dependencies → static files →
   migrations, which also auto-creates the staff user from
   `ADMIN_EMAIL`/`ADMIN_PASSWORD`.
5. Check `https://<service>.onrender.com/api/health/` →
   `{"status": "healthy", "database": "ok"}`, then browse
   `https://<service>.onrender.com/api/docs/`.

### Deploying without the Blueprint

If you prefer creating the service by hand, use:

- **Build command:** `./build.sh`
- **Start command:** `gunicorn config.wsgi:application -c gunicorn.conf.py`
- **Health check path:** `/api/health/`
- **Environment:** `DJANGO_SETTINGS_MODULE=config.settings.production`,
  `SECRET_KEY`, `DATABASE_URL` (from the database's *Internal* URL),
  `PYTHON_VERSION=3.13.14`, plus the Cloudinary / `ADMIN_*` /
  `CORS_ALLOWED_ORIGINS` values above.

### Keeping the free instance warm (cron-job.org)

Render's free web services **spin down after 15 minutes without inbound
traffic**, and the next request takes ~1 minute to wake them. A scheduled ping
keeps the API responsive. The deployment uses
[cron-job.org](https://console.cron-job.org/) as the scheduler.

**Ping `/api/health/live/`, not `/api/health/`.** The two probes exist for
this exact reason:

| Endpoint | Does | Use it for |
| --- | --- | --- |
| `/api/health/live/` | returns `{"status": "alive"}`, no database | `healthCheckPath`, every keep-alive ping |
| `/api/health/` | runs `SELECT 1` | uptime monitors, manual checks |

A database-backed ping every 10 minutes would keep the Neon compute awake:
`0.25 CU × 730 h ≈ 180 CU-hours` against the free plan's ~100 CU-hours, and
Neon suspends the whole project for the rest of the month when that runs out.
Neon resumes from a suspend in milliseconds, so there is nothing to keep warm
there — only the web instance is worth pinging. For the same reason the
Blueprint sets `healthCheckPath: /api/health/live/`: Render probes every few
seconds, which would pin the database awake 24/7 otherwise.

#### Setup on cron-job.org

**Job 1 — keep-alive** (every 10 minutes):

| Field | Value |
| --- | --- |
| Title | `warm-up` |
| URL | `https://<your-service>.onrender.com/api/health/live/` |
| Schedule | *Every 10 minutes* (custom: `*/10 * * * *`) |
| Request method | `GET` |
| Headers | none |

Notes straight from cron-job.org's FAQ, which matter here:

- **A job that is awake answers in ~2 ms**, so its 30-second request timeout is
  a non-issue — but the *first* ping after a spin-down can take ~1 minute and
  will then be recorded as a failure. Wake the instance once by hand (open the
  URL in a browser) before relying on the schedule.
- **cron-job.org disables a job after 25 consecutive failures** — useful as a
  dead-man's switch, but check the *Last executions* list if a job ever stops.
- Enable the failure email notification to get downtime alerts for free.
- It runs from a fixed set of IPs (`116.203.134.67`, `116.203.129.16`,
  `23.88.105.37`, `128.140.8.200`, `91.99.23.109` — machine-readable at
  `https://api.cron-job.org/executor-nodes.json`). IP allow-listing is not
  available on Render's free plan, so the endpoints stay protected by their own
  secret rather than by source IP.

#### Real scheduled work (`/api/v1/internal/cron/...`)

Maintenance jobs are exposed as token-guarded endpoints, so cron-job.org can
run them without paying for a Render cron job. Authentication is the shared
secret `CRON_SECRET` sent in the **`X-Cron-Secret`** header
(*Create cronjob → Advanced → custom headers*). Query parameters are
deliberately not accepted: access logs record the full request line, which
would write the secret into the log stream.

| Job URL | Does |
| --- | --- |
| `/api/v1/internal/cron/tokens/` | deletes expired JWT rows (blacklist entries cascade) — run daily |
| `/api/v1/internal/cron/sessions/` | deletes expired Django sessions (one per admin login) — run daily |

`GET` and `POST` behave identically. Responses use the API's status envelope:

```json
{"status": "success", "message": "Cron job 'tokens' completed.", "statusCode": 200,
 "data": {"job": "tokens", "expired_tokens": 3, "blacklist_entries": 1}}
```

Guard behaviour:

| Situation | Response |
| --- | --- |
| `CRON_SECRET` unset or shorter than 16 characters | `503` — endpoints are disabled (they fail closed) |
| `X-Cron-Secret` missing or wrong | `403` |
| Unknown job name | `404` (checked *after* the secret, so strangers cannot enumerate jobs) |

**Job 2 — daily cleanup** (03:00 server-local time):

| Field | Value |
| --- | --- |
| Title | `token-cleanup` |
| URL | `https://<your-service>.onrender.com/api/v1/internal/cron/tokens/` |
| Schedule | `0 3 * * *` (cron-job.org schedules in **your account's timezone** — set it to UTC or adjust) |
| Request method | `POST` |
| Header | `X-Cron-Secret: <the value from Render → Environment → CRON_SECRET>` |

Add a second job with the same header for `sessions/` if you want it cleaned
too. `render.yaml` generates `CRON_SECRET` with `generateValue: true`, so copy
it out of the Render dashboard. To add a new job, register a function in
`JOBS` (`apps/common/cron.py`) — the URL, docs entry, and guard come for free.
`.github/workflows/keepalive.yml` remains in the repo as a **manual** fallback
(no schedule, so it cannot double up on cron-job.org or burn Actions minutes).

#### Watch the instance-hour budget

The free plan gives **750 instance-hours/month per workspace**, shared across
*all* free services, and Render suspends every free service until the next
month once they are gone. Keeping one service permanently awake is ~730 hours
— it fits, but only one. If another project (`futsal-be`) lives in the same
workspace, do not keep both warm: either let this one sleep, or upgrade one
service to `starter` ($7/month), which removes spin-down entirely.

### Production environment variables

| Variable | Required | Notes |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | yes | `config.settings.production` |
| `SECRET_KEY` | yes | `generateValue: true` in the Blueprint; a `django-insecure` value aborts the boot |
| `DATABASE_URL` | yes | Neon **pooled** URL (`-pooler` host); boot fails without it |
| `DATABASE_URL_UNPOOLED` | yes on Neon | Neon **direct** URL; used only for `migrate` in `build.sh` |
| `CONN_MAX_AGE` / `CONN_HEALTH_CHECKS` | no | Defaults `600` / `true`; health checks matter because Neon closes idle connections when the compute suspends |
| `CLOUDINARY_*` | strongly advised | Without them uploads land on the instance's ephemeral disk and vanish on redeploy |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | once | Staff user created on the first `migrate` |
| `CORS_ALLOWED_ORIGINS` | yes for a browser frontend | e.g. `https://shop.example.com` |
| `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` | custom domains only | `*.onrender.com` is trusted automatically via `RENDER_EXTERNAL_HOSTNAME` |
| `SECURE_SSL_REDIRECT` | no | Default `true`; Render terminates TLS and forwards `X-Forwarded-Proto` |
| `WEB_CONCURRENCY` / `GUNICORN_THREADS` / `GUNICORN_TIMEOUT` | no | Gunicorn tuning, sensible defaults in `gunicorn.conf.py` |
| `CRON_SECRET` | for cron jobs | Shared secret (`X-Cron-Secret` header) for `/api/v1/internal/cron/...`; `< 16` chars disables them |
| `LOG_LEVEL` | no | Default `INFO`; logs go to stdout |

### Platform notes

- **Migrations run in the build.** Render's `preDeployCommand` is a paid-plan
  feature; on a paid plan move `migrate` there and drop it from `build.sh` —
  point it at `DATABASE_URL_UNPOOLED` (the direct endpoint) for the same
  reason `build.sh` does.
- **Free plan:** the service sleeps after 15 minutes idle (30–60 s cold
  start); the Neon compute also suspends when idle and resumes in a fraction
  of a second. A Render free-plan Postgres is not used here, so its 30-day
  expiry does not apply.
- **Neon branching:** to test a risky migration safely, branch the Neon
  project and point `DATABASE_URL` at the branch endpoint — preview
  environments get their own copy of the data.
- **Rotating the database password** is a two-step change: reset it in the
  Neon console, then update `DATABASE_URL` / `DATABASE_URL_UNPOOLED` in the
  Render dashboard and redeploy.
- **Custom domain:** set `ALLOWED_HOSTS=api.example.com` and
  `CSRF_TRUSTED_ORIGINS=https://api.example.com` — the latter is required for
  the session-based Django admin login; the API itself is JWT-based.
- **Static files** are served by WhiteNoise from `collectstatic`'s
  `staticfiles/` (hashed, compressed). Media lives on Cloudinary.
- **Health probe** runs `SELECT 1`; a database outage makes Render hold
  traffic back from the instance instead of serving 500s.

### Production settings summary

- Set `DJANGO_SETTINGS_MODULE=config.settings.production`.
- Enforced: `DEBUG=False`, SSL redirect + HSTS (1 year, preload), secure
  cookies, `X-Content-Type-Options`, `Referrer-Policy`, WhiteNoise manifest
  static files, PostgreSQL-only guard, persistent DB connections
  (`CONN_MAX_AGE=600` + health checks), structured console logging.
- Serving by hand (any host) works too:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py collectstatic --noinput
DATABASE_URL="$DATABASE_URL_UNPOOLED" python manage.py migrate   # direct endpoint
gunicorn config.wsgi:application -c gunicorn.conf.py
```

## Deliberately out of scope

Customer auth/accounts, carts, checkout, orders, payments, inventory/stock,
shipping, coupons, wishlists, and WhatsApp API integration are **not** part of
this backend — the frontend handles selection → cart → WhatsApp. Prices sent by
any future order flow must always be re-validated server-side.
