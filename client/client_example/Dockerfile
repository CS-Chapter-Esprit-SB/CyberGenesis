FROM python:3.12-slim

# Install uv inside container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml README.md ./

# Generate lockfile on-the-fly and install dependencies
RUN uv sync --no-cache

# Copy remaining source code
COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "client_example.main"]
