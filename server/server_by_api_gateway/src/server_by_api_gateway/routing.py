"""Static routing table mapping gateway prefixes to downstream services.

Each route forwards a request whose path starts with ``prefix`` to the
configured downstream ``target`` base URL. When ``strip_prefix`` is set the
gateway prefix is removed before forwarding (used when the downstream
endpoints are not namespaced); otherwise the original path is preserved so
the downstream service resolves its own endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass

from server_by_api_gateway.config import settings


@dataclass(frozen=True)
class Route:
    name: str
    prefix: str
    target: str
    strip_prefix: bool = False


ROUTES: tuple[Route, ...] = (
    Route("auth", "/api/v1/auth", settings.auth_service_url),
    Route(
        "rate_limiter",
        "/api/v1/ratelimit",
        settings.rate_limiter_service_url,
        strip_prefix=True,
    ),
    Route("url_shortener", "/urls", settings.url_shortener_service_url),
)


def target_for(path: str) -> tuple[Route, str] | None:
    """Return the matching route and the path to forward downstream."""
    for route in ROUTES:
        if path == route.prefix or path.startswith(route.prefix + "/"):
            remainder = path[len(route.prefix) :]
            forwarded = "" if route.strip_prefix else path
            return route, forwarded or remainder
    return None
