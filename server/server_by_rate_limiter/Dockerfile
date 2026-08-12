# Build shared base first (from repo root):
#   docker build -f server/Dockerfile.base -t cygen/python-base:uv server/
# CI / local build (service dir context):
#   docker build server/server_by_rate_limiter --file server/server_by_rate_limiter/Dockerfile

FROM cygen/python-base:uv AS builder

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN uv sync --no-dev --no-editable --no-cache

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

EXPOSE 8002

CMD ["server-by-rate-limiter"]
