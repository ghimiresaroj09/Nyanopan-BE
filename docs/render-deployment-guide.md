# Render deployment guide

How this backend is deployed: **Render** runs the web service, **Neon** hosts
Postgres, **Cloudinary** stores uploaded images, WhiteNoise serves static
files, and **cron-job.org** drives the scheduled jobs. Nothing here needs a
paid Render plan.

| | |
| --- | --- |
| Service type | Web service, Python runtime |
| Region | Singapore (matches the Neon endpoint's region) |
| Build command | `bash build.sh` |
| Start command | `gunicorn config.wsgi:application -c gunicorn.conf.py` |
| Health check path | `/api/health/live/` |
| Database | Neon Postgres (external; not provisioned by Render) |
| Media | Cloudinary |
| Scheduler | cron-job.org → `/api/v1/internal/cron/…` |

---

## 0. Before you start

Accounts/values you need:

- **GitHub** — the repo Render deploys from.
- **Render** — the service (free plan is fine).
- **Neon** — project + database, with both connection strings.
- **Cloudinary** — cloud name, API key, API secret.
- **cron-job.org** — for keep-alive + jobs (optional but recommended).

Files in this repo that matter during deployment:

| File | Role |
| --- | --- |
| `render.yaml` | Blueprint: service, env vars, health check |
| `build.sh` | Build: deps → `collectstatic` → `migrate` |
| `gunicorn.conf.py` | Binds `$PORT`, worker/thread tuning, stdout logs |
| `.python-version` | Pins Python 3.13 (Render's default is now 3.14) |
| `.env.example` | Every variable the app understands |

---

## 1. Push the repository to GitHub

Render deploys from Git, so the code must be on GitHub first.

```bash
git init
git add .
git commit -m "Ecommerce API"
# check nothing sensitive is staged:
git status --porcelain | grep -E "\.env$|db\.sqlite3|staticfiles/" || echo "clean"
git remote add origin git@github.com:<you>/<repo>.git
git push -u origin main
```

`.gitignore` already excludes `.env`, `db.sqlite3`, `/staticfiles/`, `/media/`,
`/test_media/` and `__pycache__`. `.env.example` is committed on purpose.

Two details that have bitten this project:

- **`build.sh` must keep its executable bit** if you ever change the build
  command to `./build.sh`. The Blueprint uses `bash build.sh`, which does not
  depend on the mode bit.
- **`INSTALLED_APPS` order is load-bearing** — see the troubleshooting entry on
  `collectstatic` below.

---

## 2. Neon database

The service expects **two** connection strings pointing at the same database:

| Variable | Endpoint | Used for |
| --- | --- | --- |
| `DATABASE_URL` | host contains `-pooler` | all application traffic |
| `DATABASE_URL_UNPOOLED` | host without `-pooler` | `migrate` in `build.sh` |

Why both: Neon fronts Postgres with PgBouncer in *transaction* mode, which does
not support session-level state that schema migrations can rely on. Neon's own
guidance is to run migrations over a direct connection and serve traffic over
the pooled one.

Get them from **Neon Console → project → Connect**: pick the pooled connection
string, copy it, then switch to the direct one and copy again. Both include
`?sslmode=require`.

Notes:

- Neon free scales to zero after **5 minutes idle** (cannot be disabled) and
  grants **~100 CU-hours/month**. The app is built for this: connection health
  checks are on, and the keep-alive ping deliberately does **not** touch the
  database.
- For a risky migration, branch the Neon project and point a test deploy's
  `DATABASE_URL` at the branch.

---

## 3. Create the service on Render

### Option A — Blueprint (recommended)

1. Render Dashboard → **New +** → **Blueprint**.
2. Pick the repo. Render reads `render.yaml`.
3. It generates `SECRET_KEY` and `CRON_SECRET`, sets
   `DJANGO_SETTINGS_MODULE`, Python version, worker counts and
   `healthCheckPath`, then prompts for everything marked `sync: false`.
4. Fill the prompted values (the full table is in §3.3) and click **Apply**.

### Option B — manual web service

Create a **Web Service** and enter:

| Field | Value |
| --- | --- |
| Language / runtime | Python |
| Region | Singapore |
| Build command | `bash build.sh` |
| Start command | `gunicorn config.wsgi:application -c gunicorn.conf.py` |
| Health check path | `/api/health/live/` |

Then add the environment variables below.

### 3.3 Environment variables

| Variable | Value | Notes |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Hard-required; the Blueprint sets it |
| `SECRET_KEY` | *(generate)* | A `django-insecure…` value aborts startup by design |
| `DATABASE_URL` | Neon **pooled** URL | Boot fails without a Postgres URL |
| `DATABASE_URL_UNPOOLED` | Neon **direct** URL | Used only by `migrate` |
| `CRON_SECRET` | *(generate, ≥16 chars)* | Shared secret for `/api/v1/internal/cron/…` (`X-Cron-Secret` header) |
| `PYTHON_VERSION` | `3.13.14` | Must be fully qualified when set as an env var |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | from Cloudinary | Without them uploads land on the ephemeral disk and vanish on redeploy |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | *(your choice)* | Staff user created by the first `migrate` |
| `CORS_ALLOWED_ORIGINS` | e.g. `https://shop.example.com` | Required before a browser frontend can call the API |
| `WEB_CONCURRENCY` / `GUNICORN_THREADS` | `2` / `4` | Gunicorn tuning |
| `SECURE_SSL_REDIRECT` | `true` | Default; Render terminates TLS |
| `MAX_IMAGE_UPLOAD_MB` | `5` | Per-image upload limit |
| `ALLOWED_HOSTS` | custom domain only | `*.onrender.com` is added automatically from `RENDER_EXTERNAL_HOSTNAME` |
| `CSRF_TRUSTED_ORIGINS` | custom domain only | `https://api.example.com` — needed for the session-based Django admin login |
| `LOG_LEVEL` | `INFO` | Logs go to stdout, which Render captures |

---

## 4. What the first deploy does

`build.sh` runs, in order:

1. `pip install -r requirements.txt` (fails the deploy on any dependency error)
2. `python manage.py collectstatic --no-input` — copies ~164 files and writes
   the WhiteNoise manifest (`staticfiles.json`)
3. `python manage.py migrate` on the **direct** Neon endpoint — applies all
   migrations and seeds the staff user from `ADMIN_EMAIL`/`ADMIN_PASSWORD`

Then Render starts gunicorn, which binds `$PORT` and, once
`/api/health/live/` answers `200`, switches traffic to the new instance.

Expected tail of the build log:

```
164 static files copied to '/opt/render/project/src/staticfiles', 474 post-processed.
Running migrations on the direct (unpooled) Neon endpoint.
  Applying … OK
Seeded admin user 'you@example.com'.
Build finished: dependencies installed, static files collected, migrations applied.
```

Migrations run in the build because Render's `preDeployCommand` is a paid-plan
feature. On a paid plan, move `migrate` there (using `DATABASE_URL_UNPOOLED`)
and drop it from `build.sh`.

---

## 5. Verify the deployment

Replace `$SVC` with `https://<service>.onrender.com`.

```bash
SVC=https://<service>.onrender.com

curl -s $SVC/api/health/live/      # {"status": "alive"}            (no DB)
curl -s $SVC/api/health/           # {"status": "healthy", ...}    (DB + app)
curl -o /dev/null -w '%{http_code}\n' $SVC/api/docs/               # 200 — Swagger
curl -o /dev/null -w '%{http_code}\n' $SVC/api/schema/             # 200 — OpenAPI
curl -s $SVC/api/v1/products/      # public catalog JSON
curl -s -X POST $SVC/api/v1/admin/auth/login/ \
     -H 'Content-Type: application/json' \
     -d '{"email":"you@example.com","password":"…"}'               # access token
```

Also open `$SVC/admin/` — if the admin renders with CSS, static files are
being served correctly by WhiteNoise (a bare page means `collectstatic` output
is missing).

Checklist:

- [ ] `/api/health/live/` returns `200 {"status": "alive"}`
- [ ] `/api/health/` returns `200 {"status": "healthy", "database": "ok"}`
- [ ] `/api/docs/` loads and lists the endpoints
- [ ] Login returns a JWT; a staff-only endpoint accepts it
- [ ] `/admin/` is styled (static files served)
- [ ] An image upload returns a Cloudinary URL (not a local path)

---

## 6. Keep it warm + scheduled jobs

Free web services spin down after 15 minutes without traffic, so use
cron-job.org to ping the API — see `docs/cron-job-org-setup.md` for the
click-by-click instructions.

- **Keep-alive**: `GET $SVC/api/health/live/` every 10 minutes. Use the
  `/live/` path, never `/api/health/`: the database probe would keep the Neon
  compute awake ~24/7 and exhaust the free compute allowance.
- **Jobs**: `POST $SVC/api/v1/internal/cron/tokens/` daily with the
  `X-Cron-Secret` header (deletes expired JWT rows). `/sessions/` clears
  expired admin sessions.

Instance-hour budget: **750 hours/month per workspace, shared by all free
services**. One always-awake service is ~730 hours, so keep exactly one warm —
if another project lives in the same workspace, let one of them sleep or
upgrade one to `starter` ($7/month).

---

## 7. Custom domain

1. Render → service → **Settings → Custom Domains** → add `api.example.com`;
   Render provisions TLS.
2. Add to the service environment:
   - `ALLOWED_HOSTS=api.example.com`
   - `CSRF_TRUSTED_ORIGINS=https://api.example.com` ← without this the Django
     admin login fails CSRF checks; the JWT API is unaffected.
3. Redeploy (env changes require a restart).

`RENDER_EXTERNAL_HOSTNAME` is trusted automatically, so the `onrender.com`
hostname keeps working.

---

## 8. Day-two operations

| Task | How |
| --- | --- |
| Redeploy | `git push` — Render builds and deploys automatically, with zero downtime |
| Logs | Render Dashboard → service → **Logs** (app logs go to stdout) |
| Roll back | Dashboard → **Deploys** → *Redeploy* an earlier commit |
| Rotate `SECRET_KEY` | Change it in the dashboard → redeploy (invalidates all JWTs) |
| Rotate the DB password | Reset in Neon, update `DATABASE_URL` **and** `DATABASE_URL_UNPOOLED`, redeploy |
| Rotate `CRON_SECRET` | Regenerate in Render → update the header in cron-job.org |
| Backup / restore | `pg_dump "$DIRECT_URL" > backup.sql` (use the **direct** URL; PgBouncer breaks `pg_dump`) |
| Manual job run | Trigger the cron job in cron-job.org, or `curl -X POST -H "X-Cron-Secret: …" …/cron/tokens/` |
| Scale up | Switch the instance type to `starter` in the dashboard — removes spin-down and the instance-hour cap |

---

## 9. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| Build fails: `MissingFileError: admin/img/sorting-icons.svg` | `django.contrib.staticfiles` was listed **after** `cloudinary_storage` in `INSTALLED_APPS`. Django lets the earlier app's management command win, and the Cloudinary package ships a `collectstatic` whose `copy_file()` is a no-op unless static files live on Cloudinary — so nothing is copied and manifest post-processing fails. Keep `django.contrib.staticfiles` **before** the Cloudinary apps. |
| Build fails: `DATABASE_URL` unbound / missing | `DATABASE_URL` is not set on the service, or the env var was added after the deploy started. Re-run the deploy. |
| Boot fails: `ImproperlyConfigured: strong SECRET_KEY …` | `SECRET_KEY` is unset or still a `django-insecure…` placeholder. |
| Boot fails: `PostgreSQL (DATABASE_URL) is required in production` | `DATABASE_URL` is empty or points at sqlite. |
| Deploy never goes live; log shows `Service Unavailable` | `/api/health/`-style checks hitting the DB will hold traffic back if Neon is unreachable. Confirm the health path is `/api/health/live/` and the Neon URLs are correct. |
| `502 Bad Gateway` | gunicorn died at boot — check the logs; usually a bad env var or a missing module (the start command must stay `gunicorn config.wsgi:application …`). |
| `DisallowedHost` in the logs | A custom domain (or the health-check Host header) is missing from `ALLOWED_HOSTS`. |
| Admin login → CSRF 403 | Add `CSRF_TRUSTED_ORIGINS=https://<domain>` and redeploy. |
| Static files unstyled (admin/docs) | `collectstatic` output missing — check the build log for the file count; re-run the deploy after fixing the `INSTALLED_APPS` order. |
| Uploaded images disappear after a deploy | Cloudinary credentials are not set, so files were written to the instance's ephemeral disk. |
| `/api/v1/internal/cron/…` returns `503` | `CRON_SECRET` is unset or shorter than 16 characters — the endpoints fail closed. |
| `/api/v1/internal/cron/…` returns `403` | Wrong/missing `X-Cron-Secret` header in cron-job.org. |
| First request after a quiet period takes ~1 minute | Normal free-plan cold start. Add the keep-alive ping (§6). |
| All free services suspended mid-month | The workspace's 750 instance-hours are exhausted (usually several services kept warm). Upgrade one service or let one sleep until the month resets. |
| `PYTHON_VERSION` deploy error | It must be fully qualified when set as an env var (`3.13.14`), or omit it and rely on `.python-version`. |

---

## 10. Free-tier limits at a glance

| Resource | Free allowance | Consequence |
| --- | --- | --- |
| Render web service | 750 instance-hours/month per workspace | One always-warm service fits; two do not |
| Render spin-down | after 15 min idle | ~1 min cold start; keep-alive ping recommended |
| Render one-off jobs / SSH | not available on free | use the token-guarded cron endpoints instead |
| Neon compute | ~100 CU-hours/month, scale-to-zero after 5 min | Keep keep-alive pings off the database |
| Neon storage | 0.5 GB | Watch product image counts (images live on Cloudinary) |
| cron-job.org | free, 1-minute minimum interval | 30 s request timeout; jobs auto-disable after 25 straight failures |
