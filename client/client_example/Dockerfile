FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy metadata first
COPY pyproject.toml README.md ./

# Install external dependencies only (cached if pyproject.toml hasn't changed)
RUN uv sync --no-install-project --no-cache

# Copy source code
COPY src/ ./src/

# Install the local package itself
RUN uv sync --no-cache

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "client_example.main"]
