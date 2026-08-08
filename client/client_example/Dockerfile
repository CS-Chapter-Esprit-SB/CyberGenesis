# Multi-stage build for client_example.
# Build from the monorepo root (requires cygen/python-base:uv):
#   docker build -f Dockerfile.base -t cygen/python-base:uv .
#   docker build -f client/client_example/Dockerfile -t cygen/client-example:local .

FROM cygen/python-base:uv AS builder

WORKDIR /app

# Workspace lock lives at the repo root; install only this member.
COPY pyproject.toml uv.lock ./
COPY client/client_example/pyproject.toml client/client_example/pyproject.toml
COPY client/client_example/src client/client_example/src

# pyproject declares readme = "README.md"; *.md is dockerignored, so create it here
RUN touch client/client_example/README.md \
    && uv sync --frozen --package client-example --no-dev --no-editable

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

CMD ["client-example"]
