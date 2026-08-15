"""API Gateway service package."""

import uvicorn

from server_by_latifa.config import settings


def main() -> None:
    """Entry point: start the API Gateway with uvicorn."""
    uvicorn.run(
        "server_by_latifa.main:app",
        host=settings.host,
        port=settings.port,
    )
