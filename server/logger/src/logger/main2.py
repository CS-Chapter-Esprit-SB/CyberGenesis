from logger import get_logger

logger = get_logger()

logger.info("user logged in", user_id=42, ip="10.0.0.1")
logger.warning("rate limit approaching", user_id=42, remaining=5)

logger.set_level("debug")  # <-- change the log level here

logger.error("payment failed", order_id="ord_123", reason="card_declined")
logger.debug("cache miss", key="session:42")
