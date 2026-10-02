# URL Shortener API

A production-grade URL shortening service built to go beyond "it works on my machine" — designed, load-tested, debugged under real traffic, and deployed live.

> **Status:** Backend complete. Frontend is currently in progress — coming soon.

## What it does

POST a long URL, get back a short code. Hitting the short code redirects to the original URL and logs the click asynchronously for later analytics — total clicks and clicks-per-day, queryable per link.

## Tech stack

- **API:** FastAPI, served via Gunicorn + Uvicorn workers
- **Database:** PostgreSQL, via SQLAlchemy ORM + Alembic migrations
- **Connection pooling:** PgBouncer (transaction-mode pooling)
- **Cache:** Redis — caches `short_code → URL` lookups (1hr TTL) for fast redirects
- **Async processing:** Celery (Redis-backed) — click logging happens off the request path
- **Auth:** JWT (PyJWT), password hashing via passlib/bcrypt
- **Infra:** Docker, Docker Compose (local), deployed on Railway

## Architecture

```
Client
  │
  ▼
FastAPI (Gunicorn + multiple Uvicorn workers)
  │
  ├──► Redis ──► short_code → URL cache (redirect hot path)
  │
  ├──► PgBouncer ──► PostgreSQL  (links, users, clicks)
  │
  └──► Celery (via Redis queue) ──► async click logging ──► PostgreSQL
```

Redirects check Redis first; a cache miss falls through to Postgres (via PgBouncer) and repopulates the cache. Every redirect also enqueues a background job to record the click — the response to the user doesn't wait on that write.

## API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/register` | — | Create a user account |
| `POST` | `/login` | — | Returns a JWT access token (form-encoded, OAuth2 password flow) |
| `POST` | `/shorten_url` | Bearer token | Shorten a URL for the authenticated user |
| `GET` | `/{short_code}` | — | Redirect to the original URL (307); logs the click async |
| `GET` | `/links/{short_code}/stats` | — | Click count + daily click aggregates for a link |
| `GET` | `/health` | — | Liveness check |

Interactive API docs (Swagger UI) are available at `/docs` on any running instance.

## Load testing — the part most projects skip

The first real load test exposed a genuine bottleneck: throughput collapsed past ~70 concurrent users and kept degrading the longer load was held. `docker stats` showed Postgres pinned at 700%+ CPU while every other service sat idle — traced to a duplicate-URL check with no index on the columns it filtered on, meaning every request did a full table scan that got slower as the table grew.

**Fix:** added a composite index on `links(user_id, long_url)` and introduced PgBouncer for connection pooling.

**Result**, re-verified with a full, continuous 1-hour sustained test:

| Metric | Result |
|---|---|
| Duration | 1 hour (continuous) |
| Total requests | 6,156,522 |
| Error rate | 0% |
| Sustained throughput | ~1,598 req/s average |
| Daily capacity (extrapolated) | ~138M req/day at that rate |

## Running locally

Requires Docker and Docker Compose.

1. Clone the repo and create a `.env` file (see **Environment variables** below).
2. ```bash
   docker compose up --build
   ```
   This builds the app, applies Alembic migrations automatically, and starts all five services (web, Postgres, Redis, PgBouncer, Celery worker).
3. Check it's alive:
   ```bash
   curl http://localhost:8000/health
   ```

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string — should point at PgBouncer (`pgbouncer:6432`), not Postgres directly |
| `REDIS_URL` | Redis connection string (used for both caching and the Celery broker/backend) |
| `SECRET_KEY` | JWT signing secret — **must** be set explicitly to a long, random value (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`). Do not rely on any default. |

## Deployment

Deployed on Railway as separate services: managed PostgreSQL, managed Redis, PgBouncer (from the `edoburu/pgbouncer` image), the FastAPI app, and a dedicated Celery worker — each wired together via Railway's internal networking and reference variables.

## Database schema

**`links`**
- `id`, `short_code` (unique, indexed), `long_url`, `created_at`, `user_id` (FK → `users.id`)
- Composite index on `(user_id, long_url)` for fast duplicate-link lookups

**`clicks`**
- `id`, `link_id` (FK → `links.id`, cascade delete), `created_at`, `ip_hash`, `referrer`

## Roadmap

- [x] Core API: create, redirect, stats
- [x] Redis caching for redirects
- [x] Async click logging via Celery
- [x] Alembic migrations
- [x] Load tested and tuned for sustained high throughput
- [x] Deployed (Railway)
- [ ] Frontend — in progress