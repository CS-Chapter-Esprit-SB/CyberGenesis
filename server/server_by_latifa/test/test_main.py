"""Unit tests for the API Gateway service."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from server_by_latifa.config import settings
from server_by_latifa.main import DownstreamServiceError, _forward_request, app

client = TestClient(app)


def test_health_check() -> None:
    """The /health endpoint should return status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_service_returns_404() -> None:
    """Routing to an unregistered service name should return 404."""
    response = client.get("/unknown-service/some-path")
    assert response.status_code == 404
    assert "Unknown service" in response.json()["detail"]


def test_successful_routing_to_downstream() -> None:
    """A successful downstream response should be forwarded as-is."""
    mock_response = httpx.Response(
        status_code=200,
        json={"message": "hello"},
        request=httpx.Request("GET", "http://localhost:8001/ping"),
    )

    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=AsyncMock(return_value=mock_response),
    ):
        response = client.get("/auth/ping")

    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_downstream_5xx_triggers_retry_then_fails() -> None:
    """A persistent 5xx from downstream should exhaust retries and return 502."""
    mock_response = httpx.Response(
        status_code=503,
        text="service unavailable",
        request=httpx.Request("GET", "http://localhost:8001/ping"),
    )

    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=AsyncMock(return_value=mock_response),
    ):
        response = client.get("/auth/ping")

    assert response.status_code == 502
    assert "unavailable after retries" in response.json()["detail"]


def test_downstream_connection_error_triggers_retry_then_fails() -> None:
    """A connection error to downstream should exhaust retries and return 502."""
    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=AsyncMock(side_effect=httpx.ConnectError("connection refused")),
    ):
        response = client.get("/rate-limiter/check")

    assert response.status_code == 502


@pytest.mark.asyncio
async def test_forward_request_raises_on_5xx() -> None:
    """_forward_request should raise DownstreamServiceError on a 5xx response."""
    mock_response = httpx.Response(
        status_code=500,
        text="internal error",
        request=httpx.Request("GET", "http://localhost:8003/shorten"),
    )

    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=AsyncMock(return_value=mock_response),
    ):
        with pytest.raises(DownstreamServiceError):
            await _forward_request(
                service_name="url-shortener",
                base_url="http://localhost:8003",
                path="shorten",
                method="GET",
                headers={},
                params={},
                body=b"",
            )


def test_retry_attempts_exactly_five() -> None:
    """The gateway should retry a transient 5xx exactly retry_attempts times."""
    mock_response = httpx.Response(
        status_code=503,
        text="service unavailable",
        request=httpx.Request("GET", "http://localhost:8001/ping"),
    )
    mock_call = AsyncMock(return_value=mock_response)
    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=mock_call,
    ):
        response = client.get("/auth/ping")

    assert response.status_code == 502
    assert mock_call.call_count == settings.retry_attempts


def test_logger_error_called_on_downstream_failure() -> None:
    """StructuredLogger.error should be invoked when a downstream call fails."""
    mock_response = httpx.Response(
        status_code=503,
        text="service unavailable",
        request=httpx.Request("GET", "http://localhost:8001/ping"),
    )
    with (
        patch(
            "server_by_latifa.main.httpx.AsyncClient.request",
            new=AsyncMock(return_value=mock_response),
        ),
        patch("server_by_latifa.main.logger.error") as mock_log_error,
    ):
        response = client.get("/auth/ping")

    assert response.status_code == 502
    assert mock_log_error.called


def test_successful_routing_to_rate_limiter() -> None:
    """A successful response from the rate-limiter service should be forwarded as-is."""
    mock_response = httpx.Response(
        status_code=200,
        json={"allowed": True},
        request=httpx.Request("GET", "http://localhost:8002/check"),
    )
    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=AsyncMock(return_value=mock_response),
    ):
        response = client.get("/rate-limiter/check")
    assert response.status_code == 200
    assert response.json() == {"allowed": True}


def test_successful_routing_to_url_shortener() -> None:
    """A successful response from url-shortener should be forwarded as-is."""
    mock_response = httpx.Response(
        status_code=200,
        json={"short_url": "http://short.link/abc"},
        request=httpx.Request("GET", "http://localhost:8003/shorten"),
    )
    with patch(
        "server_by_latifa.main.httpx.AsyncClient.request",
        new=AsyncMock(return_value=mock_response),
    ):
        response = client.get("/url-shortener/shorten")
    assert response.status_code == 200
    assert response.json() == {"short_url": "http://short.link/abc"}


def test_gateway_listens_on_configured_port() -> None:
    """The gateway's default configured port should be 8000 per the ticket."""
    assert settings.port == 8000
