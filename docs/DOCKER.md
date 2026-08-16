# Docker images

Shared Docker infrastructure lives under [`server/`](../server/). Per-service application images live next to each microservice (`server/<service>/Dockerfile`). CI builds a service Dockerfile only when one exists in that service folder and is non-empty.

## Roles

| File | Role |
|------|------|
| [`server/Dockerfile.base`](../server/Dockerfile.base) | Optional **builder** image: Python 3.12 + `uv` only (no app code). Service Dockerfiles install `uv` inline; this file is for local caching only. |
| [`server/Dockerfile.template`](../server/Dockerfile.template) | **Multi-stage** example to copy into `server/<service>/Dockerfile` when a service is ready. Not built by CI (filename is not `Dockerfile`). |
| `server/<service>/Dockerfile` | Self-contained multi-stage image: `python:3.12-slim` builder with `uv`, then slim runtime with `.venv` only. |
| [`server/docker-compose.yml`](../server/docker-compose.yml) | Postgres, Redis, and application services (auth, rate-limiter, url-shortener). |
| [`server/.env.example`](../server/.env.example) | Example env vars for Compose. |

`Dockerfile.base` is not a runnable service and is **not** required for CI or Compose service builds.

## Why multi-stage?

- **Builder stage** (`python:3.12-slim` + `uv`): resolve dependencies and install the package into `.venv`.
- **Runtime stage** (`python:3.12-slim`): copy only `.venv` — smaller image, no `uv` / build tools.

## Optional: shared builder cache

To avoid reinstalling `uv` on every local rebuild, you can tag the shared base:

```bash
docker build -f server/Dockerfile.base -t cygen/python-base:uv server/
```

Service Dockerfiles do not `FROM` this image; they embed the same steps so CI and fresh clones work without a private registry.

## Multi-stage service template

1. Copy [`server/Dockerfile.template`](../server/Dockerfile.template) to `server/<service>/Dockerfile`.
2. Adjust `COPY` paths / `uv sync` / `CMD` for that package.
3. Build with the same context CI uses once the file is non-empty:

```bash
docker build server/<service> --file server/<service>/Dockerfile
```

Until then, leave `Dockerfile` **empty** so CI skips (`-s` requires size > 0).

## Compose (infra + services)

From `server/` (or repo root with `-f`):

```bash
cd server
cp .env.example .env   # if needed
docker compose up -d --build
```

Services:

| Service | Port | Depends on |
|---------|------|------------|
| `api-gateway` | 8080 (host) → 8000 (container) | Auth, Rate Limiter, URL Shortener |
| `url-shortener` | 8000 | Postgres |
| `auth` | 8001 | Postgres |
| `rate-limiter` | 8002 | Redis |
| `postgres` | 5432 | — |
| `redis` | 6379 | — |

Or from the repo root:

```bash
docker compose -f server/docker-compose.yml --env-file server/.env.example up -d --build
```

## Gateway middleware stack

The `api-gateway` service routes requests by prefix to the downstream services and applies bounded retries. The middleware below is the next step to mount at the gateway edge. Both packages export ASGI middleware meant to be mounted in front of any downstream app:

```text
Request → RateLimitMiddleware → JWTAuthMiddleware → downstream ASGI app
```

**Rate limiting** (`server_by_rate_limiter.middleware`):

- `RedisSlidingWindowLimiter` — sliding-window over Redis sorted sets
- `RateLimitMiddleware` — enforces limits keyed by `client_ip`, `bearer_token`, or `gateway_identifier` (token when present, otherwise IP)
- Returns `429` with `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After`

**JWT authentication** (`server_by_auth.middleware`):

- `JWTAuthMiddleware` — blocks requests without a valid `Authorization: Bearer <token>` header
- Public paths: `/health`, `/docs`, `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/verify`
- Injects `X-User-Id` and `X-Username` into the **request scope** for downstream services

Example wiring in the gateway app:

```python
from server_by_auth.middleware import JWTAuthMiddleware
from server_by_rate_limiter.middleware import RateLimitMiddleware, gateway_identifier
from server_by_rate_limiter.ratelimit import RedisSlidingWindowLimiter
from server_by_rate_limiter.redis_client import redis_client

limiter = RedisSlidingWindowLimiter(redis_client, scope="gateway", limit=100, window_ms=60_000)
downstream = JWTAuthMiddleware(url_shortener_app)
gateway = RateLimitMiddleware(downstream, limiter, gateway_identifier)
```

`server_by_auth.main.create_gateway_app(downstream)` wraps a downstream app with JWT auth only.
