from __future__ import annotations

import json
import logging
import time
from typing import Any


class RecordingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class StructuredLogger:
    def __init__(self, name: str = "service", level: int = logging.INFO) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        self.logger.handlers.clear()
        self.handler = RecordingHandler()
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(self.handler)

    @staticmethod
    def _build_payload(event: str, **context: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "timestamp": int(time.time()),
            "event": event,
        }
        payload.update(context)
        return payload

    def warning(self, event: str, **context: Any) -> None:
        payload = json.dumps(self._build_payload(event, **context), default=str)
        self.logger.warning(payload)

    def info(self, event: str, **context: Any) -> None:
        payload = json.dumps(self._build_payload(event, **context), default=str)
        self.logger.info(payload)
