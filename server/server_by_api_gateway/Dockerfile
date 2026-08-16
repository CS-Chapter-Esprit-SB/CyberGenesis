# CI / local build (service dir context):
#   docker build server/server_by_api_gateway --file server/server_by_api_gateway/Dockerfile

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/0.11.21/install.sh | sh \
    && ln -sf /root/.local/bin/uv /usr/local/bin/uv

COPY pyproject.toml ./
COPY src ./src

RUN uv sync --no-dev --no-editable --no-cache

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

EXPOSE 8000

CMD ["server-by-api-gateway"]
