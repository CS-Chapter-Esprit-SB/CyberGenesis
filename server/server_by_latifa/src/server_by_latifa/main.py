"""API Gateway entrypoint: routes client requests to downstream microservices,
with retry logic and structured error logging on transient failures."""

from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from server_by_latifa.config import settings
from server_by_latifa.logger import StructuredLogger

app = FastAPI(title="CyberGenesis API Gateway")
logger = StructuredLogger(name="api-gateway")


class DownstreamServiceError(Exception):
    """Raised when a downstream service returns a transient (5xx) failure."""

    def __init__(self, service: str, status_code: int, detail: str) -> None:
        self.service = service
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@retry(
    reraise=True,
    stop=stop_after_attempt(settings.retry_attempts),
    wait=wait_fixed(settings.retry_wait_seconds),
    retry=retry_if_exception_type(DownstreamServiceError),
)
async def _forward_request(
    service_name: str,
    base_url: str,
    path: str,
    method: str,
    headers: dict[str, str],
    params: dict[str, Any],
    body: bytes,
) -> httpx.Response:
    """Forward a request to a downstream service, retrying on transient 5xx errors."""
    url = f"{base_url}/{path}"

    async with httpx.AsyncClient(timeout=settings.downstream_timeout_seconds) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                content=body,
            )
        except httpx.RequestError as exc:
            logger.error(
                "Downstream request failed (connection error)",
                service=service_name,
                url=url,
                error=str(exc),
            )
            raise DownstreamServiceError(service_name, 503, str(exc)) from exc

    if 500 <= response.status_code < 600:
        logger.error(
            "Downstream service returned a transient failure",
            service=service_name,
            url=url,
            status_code=response.status_code,
        )
        raise DownstreamServiceError(service_name, response.status_code, response.text)

    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.api_route(
    "/{service_name}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def gateway_route(service_name: str, path: str, request: Request) -> Response:
    """Route an incoming client request to the appropriate downstream service."""
    downstream = settings.downstream_services.get(service_name)

    if downstream is None:
        logger.error("Unknown downstream service requested", service=service_name)
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")

    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    try:
        response = await _forward_request(
            service_name=downstream.name,
            base_url=downstream.base_url,
            path=path,
            method=request.method,
            headers=headers,
            params=dict(request.query_params),
            body=body,
        )
    except DownstreamServiceError as exc:
        logger.error(
            "Exhausted retry attempts for downstream service",
            service=exc.service,
            status_code=exc.status_code,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Downstream service '{exc.service}' unavailable after retries",
        ) from exc

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
