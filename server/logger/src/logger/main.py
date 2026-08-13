"""
Core logging engine for CyberGenesis.

Singleton structured JSON logger for stdout (Docker-friendly),
producing records shaped for downstream Kafka ingestion.
"""

import json
import logging
import os
import sys
import uuid
from typing import cast, override

ENV_VAR_NAME = "CYBERGENESIS_LOG"
SERVICE_ID_ENV_VAR = "CYBERGENESIS_SERVICE_ID"
HANDLER_NAME = "cybergenesis_stdout_json"

LOG_LEVEL_MAP: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class _JsonFormatter(logging.Formatter):
    """Formats each record as a single JSON line with the mandatory schema."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "service_id": os.getenv(SERVICE_ID_ENV_VAR, "cybergenesis"),
            "log_id": str(uuid.uuid4()),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
        }
        # Include any extra fields passed via logger.info("msg", user_id=42)
        extra_fields = cast("dict[str, object]", getattr(record, "extra_fields", {}))
        for key, value in extra_fields.items():
            payload[key] = value
        return json.dumps(payload)


class StructuredLogger:
    """Singleton JSON logger. Get the shared instance via StructuredLogger.get()."""

    _instance: "StructuredLogger | None" = None
    _handler: "logging.Handler | None" = None

    def __init__(self) -> None:
        level = LOG_LEVEL_MAP.get(
            os.getenv(ENV_VAR_NAME, "warning").strip().lower(), logging.WARNING
        )

        logger = logging.getLogger("cybergenesis")
        logger.setLevel(level)
        logger.propagate = False

        # Track our own handler by identity/name rather than checking
        # "does this logger have any handlers at all" — other code (test
        # runners, other libraries) may attach unrelated handlers to this
        # logger first, and that must never stop us from installing ours.
        if StructuredLogger._handler is None:
            handler = logging.StreamHandler(
                sys.stdout
            )  # stdout for Docker/Kafka pipelines
            handler.setFormatter(_JsonFormatter())
            handler.set_name(HANDLER_NAME)
            StructuredLogger._handler = handler

        if StructuredLogger._handler not in logger.handlers:
            logger.addHandler(StructuredLogger._handler)

        self._logger: logging.Logger = logger

    @classmethod
    def get(cls) -> "StructuredLogger":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_for_tests_only(cls) -> None:
        """Clears singleton/handler state between test cases. Test-only hook."""
        cls._instance = None
        cls._handler = None

    def set_level(self, level_name: str) -> None:
        """Change the active log level at runtime, e.g. logger.set_level("debug")."""
        level = LOG_LEVEL_MAP.get(level_name.strip().lower(), logging.WARNING)
        self._logger.setLevel(level)

    def _log(self, level: int, message: str, **fields: object) -> None:
        self._logger.log(level, message, extra={"extra_fields": fields})

    def debug(self, message: str, **fields: object) -> None:
        self._log(logging.DEBUG, message, **fields)

    def info(self, message: str, **fields: object) -> None:
        self._log(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: object) -> None:
        self._log(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: object) -> None:
        self._log(logging.ERROR, message, **fields)


def get_logger() -> StructuredLogger:
    """Usage: logger = get_logger(); logger.info("User logged in", user_id=42)"""
    return StructuredLogger.get()


__all__ = ["StructuredLogger", "get_logger"]
