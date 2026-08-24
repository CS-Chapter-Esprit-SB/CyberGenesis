"""Unit tests for logger.main — targets 100% coverage of formatting/output logic."""

from __future__ import annotations

import io
import json
import logging
import sys
import uuid
from collections.abc import Callable, Generator
from typing import cast

import pytest
from logger.main import HANDLER_NAME, StructuredLogger, get_logger


def _clear_our_handler(stdlib_logger: logging.Logger) -> None:
    """Remove only the handler this library installed, leaving any handler
    a test runner or other library attached to this same logger alone —
    mirrors what the production code itself must tolerate."""
    for h in list(stdlib_logger.handlers):
        if h.name == HANDLER_NAME:
            stdlib_logger.removeHandler(h)


@pytest.fixture(autouse=True)
def reset_logger_state(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Ensure each test starts with a clean singleton and a fresh stdlib logger."""
    StructuredLogger.reset_for_tests_only()
    stdlib_logger = logging.getLogger("cybergenesis")
    _clear_our_handler(stdlib_logger)
    stdlib_logger.setLevel(logging.NOTSET)
    monkeypatch.delenv("CYBERGENESIS_LOG", raising=False)
    monkeypatch.delenv("CYBERGENESIS_SERVICE_ID", raising=False)
    yield
    StructuredLogger.reset_for_tests_only()
    _clear_our_handler(stdlib_logger)


def _capture_stream(monkeypatch: pytest.MonkeyPatch) -> io.StringIO:
    """Patch sys.stdout before the singleton is built, and return the buffer.

    sys is a shared singleton module, so patching it here also affects the
    sys.stdout that logger.main reads when it builds its StreamHandler —
    no need to reach into logger.main's internals to do it.
    """
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    return buffer


def _last_record(buffer: io.StringIO) -> dict[str, object]:
    lines = buffer.getvalue().strip().splitlines()
    return cast("dict[str, object]", json.loads(lines[-1]))


class TestSingleton:
    def test_get_returns_same_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _ = _capture_stream(monkeypatch)
        first = StructuredLogger.get()
        second = StructuredLogger.get()
        assert first is second

    def test_get_logger_helper_uses_singleton(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _ = _capture_stream(monkeypatch)
        assert get_logger() is StructuredLogger.get()

    def test_no_duplicate_handler(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Goal: building StructuredLogger twice must not attach our handler
        # twice (which would print every log line twice). We only count
        # handlers with OUR name — not the logger's total handler count —
        # since other code (e.g. a test runner) may legitimately attach
        # its own unrelated handlers to this same logger.
        _ = _capture_stream(monkeypatch)
        _ = StructuredLogger()  # first build: attaches our handler
        _ = StructuredLogger()  # second build: should reuse it, not duplicate
        stdlib_logger = logging.getLogger("cybergenesis")
        ours = [h for h in stdlib_logger.handlers if h.name == HANDLER_NAME]
        assert len(ours) == 1

    def test_handler_survives_foreign_handler(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Goal: if something else (a test runner, another library) already
        # attached its own handler to the "cybergenesis" logger before we
        # do, our handler must still get installed and still receive logs.
        stdlib_logger = logging.getLogger("cybergenesis")
        stdlib_logger.addHandler(logging.NullHandler())  # simulate foreign handler
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("hello")
        assert buffer.getvalue() != ""  # our handler still wrote the log

    def test_logger_does_not_propagate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _ = _capture_stream(monkeypatch)
        _ = StructuredLogger.get()
        assert logging.getLogger("cybergenesis").propagate is False


class TestSchema:
    def test_default_service_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("hello")
        record = _last_record(buffer)
        assert record["service_id"] == "cybergenesis"

    def test_custom_service_id_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CYBERGENESIS_SERVICE_ID", "billing-api")
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("hello")
        record = _last_record(buffer)
        assert record["service_id"] == "billing-api"

    def test_log_id_is_valid_uuid4(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("hello")
        record = _last_record(buffer)
        log_id = record["log_id"]
        assert isinstance(log_id, str)
        parsed = uuid.UUID(log_id, version=4)
        assert str(parsed) == log_id

    def test_log_id_unique_per_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        logger.warning("first")
        logger.warning("second")
        lines = buffer.getvalue().strip().splitlines()
        ids = [json.loads(line)["log_id"] for line in lines]
        assert ids[0] != ids[1]

    def test_message_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("something happened")
        record = _last_record(buffer)
        assert record["message"] == "something happened"

    def test_mandatory_fields_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("hello")
        record = _last_record(buffer)
        for field in ("service_id", "log_id", "level", "message"):
            assert field in record

    def test_extra_fields_are_merged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CYBERGENESIS_LOG", "info")
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().info("user logged in", user_id=42, action="login")
        record = _last_record(buffer)
        assert record["user_id"] == 42
        assert record["action"] == "login"

    def test_no_extra_fields_yields_only_mandatory_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("plain message")
        record = _last_record(buffer)
        assert set(record.keys()) == {"service_id", "log_id", "level", "message"}

    def test_output_is_single_json_line(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        StructuredLogger.get().warning("hello")
        lines = buffer.getvalue().strip().splitlines()
        assert len(lines) == 1
        parsed = cast("object", json.loads(lines[0]))
        assert parsed is not None


def _call_debug(logger: StructuredLogger, msg: str) -> None:
    logger.debug(msg)


def _call_info(logger: StructuredLogger, msg: str) -> None:
    logger.info(msg)


def _call_warning(logger: StructuredLogger, msg: str) -> None:
    logger.warning(msg)


def _call_error(logger: StructuredLogger, msg: str) -> None:
    logger.error(msg)


class TestLevels:
    @pytest.mark.parametrize(
        "call,expected_level",
        [
            (_call_debug, "debug"),
            (_call_info, "info"),
            (_call_warning, "warning"),
            (_call_error, "error"),
        ],
    )
    def test_each_level_method_sets_level_field(
        self,
        monkeypatch: pytest.MonkeyPatch,
        call: Callable[[StructuredLogger, str], None],
        expected_level: str,
    ) -> None:
        monkeypatch.setenv("CYBERGENESIS_LOG", "debug")
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        call(logger, "message for " + expected_level)
        record = _last_record(buffer)
        assert record["level"] == expected_level

    def test_default_level_is_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        logger.debug("should be suppressed")
        assert buffer.getvalue() == ""
        logger.warning("should appear")
        assert buffer.getvalue() != ""

    def test_env_var_lowercases_and_strips(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CYBERGENESIS_LOG", "  INFO  ")
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        logger.info("should appear at info level")
        assert buffer.getvalue() != ""

    def test_unknown_env_value_falls_back_to_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CYBERGENESIS_LOG", "not-a-real-level")
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        logger.info("should be suppressed")
        assert buffer.getvalue() == ""
        logger.warning("should appear")
        assert buffer.getvalue() != ""

    def test_set_level_changes_filtering_at_runtime(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        logger.info("should be suppressed under default warning level")
        assert buffer.getvalue() == ""
        logger.set_level("debug")
        logger.debug("should now appear")
        record = _last_record(buffer)
        assert record["level"] == "debug"

    def test_set_level_unknown_value_falls_back_to_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        buffer = _capture_stream(monkeypatch)
        logger = StructuredLogger.get()
        logger.set_level("not-a-real-level")
        logger.info("should be suppressed")
        assert buffer.getvalue() == ""
        logger.warning("should appear")
        assert buffer.getvalue() != ""
