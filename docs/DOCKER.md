# Docker images

Shared Docker infrastructure lives under [`server/`](../server/). Per-service application images are added later next to each microservice (`server/<service>/Dockerfile`, etc.). CI is unchanged and builds a service Dockerfile only when one exists in that service folder and is non-empty.

## Roles

| File | Role |
|------|------|
| [`server/Dockerfile.base`](../server/Dockerfile.base) | Shared **builder** image: Python 3.12 + `uv` only. No app code, no project dependencies. |
| [`server/Dockerfile.template`](../server/Dockerfile.template) | **Multi-stage** example to copy into `server/<service>/Dockerfile` when a service is ready. Not built by CI (filename is not `Dockerfile`). |
| `server/<service>/Dockerfile` | Real service image (start empty so CI skips; paste from the template when ready). |
| [`server/docker-compose.yml`](../server/docker-compose.yml) | **Infra only** (Postgres + Redis). It does not build or run app images. |
| [`server/.env.example`](../server/.env.example) | Example env vars for Compose. |

`Dockerfile.base` is not a runnable service. Tag it as `cygen/python-base:uv` and use it as `FROM` in each service’s builder stage.

## Why base + multi-stage?

- **Base** (`cygen/python-base:uv`): standardizes Python + `uv` for server-side builds.
- **Builder stage**: resolve the lockfile, install the package into `.venv`.
- **Runtime stage** (`python:3.12-slim`): copy only `.venv` — smaller image, no `uv` / build tools.

## Build the shared base

From the **monorepo root** (use `sudo` if your user cannot access the Docker socket):

```bash
docker build -f server/Dockerfile.base -t cygen/python-base:uv server/
```

Optional check:

```bash
docker images | grep cygen
```

You should see `cygen/python-base`.

## Multi-stage service template

1. Copy [`server/Dockerfile.template`](../server/Dockerfile.template) to `server/<service>/Dockerfile`.
2. Adjust `COPY` paths / `uv sync` / `CMD` for that package.
3. Build with the same context CI uses once the file is non-empty:

```bash
docker build server/<service> --file server/<service>/Dockerfile
```

Until then, leave `Dockerfile` **empty** so CI skips (`-s` requires size > 0).

## Compose (infra)

```bash
cd server
cp .env.example .env   # if needed
docker compose up -d   # Postgres + Redis only
```

Or from the repo root:

```bash
docker compose -f server/docker-compose.yml --env-file server/.env.example up -d
```
