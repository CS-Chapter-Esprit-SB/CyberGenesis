import redis
from fastapi import FastAPI

from server_example.gateway import RateLimitMiddleware
from server_example.structured_logger import StructuredLogger

app = FastAPI()

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

logger = StructuredLogger("gateway")

app.add_middleware(
    RateLimitMiddleware,
    redis_client=redis_client,
    limit=2,
    window_seconds=60,
    logger=logger,
    lookup_keys=("ip", "token"),
)


@app.get("/api/test")
async def test_endpoint() -> dict[str, str]:
    return {"message": "Request accepted"}
