# Use an official lightweight Python image
FROM python:3.12-slim

# Install uv inside the container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker layer caching
COPY pyproject.toml README.md ./

# Install dependencies using uv
RUN uv sync --frozen --no-cache

# Copy application source code
COPY src/ ./src/

# Expose port (adjust if your microservice uses a different port)
EXPOSE 8000

# Run the microservice
CMD ["uv", "run", "python", "-m", "client_example.main"]
