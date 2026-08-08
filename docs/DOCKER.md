# Docker images

This repo uses a shared base image plus a multi-stage Dockerfile per microservice. That keeps builds consistent and final images small.

## Roles

| File | Role |
|------|------|
| [`Dockerfile.base`](../Dockerfile.base) | Shared **builder** image: Python 3.12 + `uv` only. No app code, no project dependencies. |
| `<service>/Dockerfile` | Multi-stage **service** image: install deps + app in a builder stage, copy only the runtime venv into a slim final image. |
| [`docker-compose.yml`](../docker-compose.yml) | **Infra only** (Postgres + Redis). It does not build or run app images. |

`Dockerfile.base` is not the runnable service. Tag it as `cygen/python-base:uv` and use it as `FROM` in each service’s builder stage.

## Why multi-stage?

- **Builder stage** (from `cygen/python-base:uv`): has `uv`, resolves the lockfile, installs the package into `.venv`.
- **Runtime stage** (from `python:3.12-slim`): copies only `.venv` (and whatever else is required to run). No `uv`, no build tools, smaller attack surface and image size.

## Test locally (`client_example`)

Always run from the **monorepo root**. Use `sudo` if your user cannot access the Docker socket.

```bash
# 1. Shared base (once, or when Dockerfile.base changes)
docker build -f Dockerfile.base -t cygen/python-base:uv .

# 2. Service image (requires the base image from step 1)
docker build -f client/client_example/Dockerfile -t cygen/client-example:local .

# 3. Run — expect: Hello from client-example!
docker run --rm cygen/client-example:local
```

Optional check:

```bash
docker images | grep cygen
```

You should see both `cygen/python-base` and `cygen/client-example`.

CI (`docker-build` in `.github/workflows/ci.yml`) follows the same order: build/tag `cygen/python-base:uv`, then `docker build -f <service>/Dockerfile .` from the repo root.

## Pattern for a new service

1. Keep using `Dockerfile.base` / `cygen/python-base:uv` as the builder parent.
2. Copy that service’s `pyproject.toml` + `src` under the same paths the workspace lock expects (for example `client/<name>/...`).
3. Sync only that workspace member (create a stub `README.md` in the image if `pyproject.toml` declares one and `*.md` is dockerignored):

   ```dockerfile
   RUN touch <layer>/<service>/README.md \
       && uv sync --frozen --package <package-name> --no-dev --no-editable
   ```

4. In the runtime stage, copy `/app/.venv` and set `PATH=/app/.venv/bin:$PATH`. Prefer the package console script (or `python -m ...`) as `CMD` — do not require `uv` in the final image.
5. Build from the repo root with `-f <layer>/<service>/Dockerfile`.

## Compose (infra)

```bash
cp .env.example .env   # if needed
docker compose up -d   # Postgres + Redis only
```

App containers are built with the Dockerfiles above, not via Compose (unless you add app services later).
