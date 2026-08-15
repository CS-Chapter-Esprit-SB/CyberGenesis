"""Minimal structured (JSON) logger for the API Gateway service."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class StructuredLogger:
    """Emits log records as single-line JSON for easy ingestion by log tools."""

    def __init__(self, name: str = "api-gateway", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.propagate = False

    def _emit(self, level: str, message: str, **context: Any) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "message": message,
            **context,
        }
        line = json.dumps(record, default=str)

        if level == "error":
            self._logger.error(line)
        elif level == "warning":
            self._logger.warning(line)
        elif level == "debug":
            self._logger.debug(line)
        else:
            self._logger.info(line)

    def info(self, message: str, **context: Any) -> None:
        self._emit("info", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self._emit("warning", message, **context)

    def error(self, message: str, **context: Any) -> None:
        self._emit("error", message, **context)

    def debug(self, message: str, **context: Any) -> None:
        self._emit("debug", message, **context)
