# CyberGenesis Logger

A tiny structured JSON logger for CyberGenesis services. Every log call
emits one JSON line to stdout — ready to be picked up by a container
runtime and shipped downstream (e.g. to Kafka) with no extra parsing.

```json
{"service_id": "payments-api", "log_id": "d43136aa-851d-4f2f-94ef-a9a0608224f6", "level": "info", "message": "user logged in", "user_id": 42}
```

## Install / import

The package lives at `src/logger`. With `src` on your `PYTHONPATH` (or
installed as a package), import it as:

```python
from logger import get_logger
```

## Quick start

```python
from logger import get_logger

logger = get_logger()

logger.info("user logged in", user_id=42, ip="10.0.0.1")
logger.warning("rate limit approaching", user_id=42, remaining=5)
logger.error("payment failed", order_id="ord_123", reason="card_declined")
logger.debug("cache miss", key="session:42")
```

`get_logger()` always returns the same shared logger instance, so you
can call it from any module in your codebase — no need to pass a
logger instance around or configure anything per-file.

## Log levels

Four methods are available, from most to least verbose:

| Method | Level |
|---|---|
| `logger.debug(...)` | `debug` |
| `logger.info(...)` | `info` |
| `logger.warning(...)` | `warning` |
| `logger.error(...)` | `error` |

A message is only printed if its level is **at or above** the logger's
current threshold. The default threshold is `warning`, so `debug` and
`info` calls are silent unless you raise the verbosity (see below).

## Adding custom fields

Pass any keyword arguments you like — they're merged straight into
the JSON output:

```python
logger.error(
    "payment failed",
    order_id="ord_123",
    reason="card_declined",
    retryable=False,
)
```

```json
{"service_id": "cybergenesis", "log_id": "...", "level": "error", "message": "payment failed", "order_id": "ord_123", "reason": "card_declined", "retryable": false}
```

There's no schema to declare upfront — whatever you pass becomes a
key in the output. Values must be JSON-serializable (strings, numbers,
booleans, `None`, lists, dicts).

## Setting the log level

### At startup, via environment variable

Set `CYBERGENESIS_LOG` before your process starts. This is the
recommended way to control verbosity in production (e.g. via your
Docker/Compose/K8s env config).

```bash
export CYBERGENESIS_LOG=debug   # debug, info, warning, error, or critical
python your_app.py
```

If unset, or set to something unrecognized, it falls back to
`warning`. The value is case-insensitive and whitespace is stripped
(`"  DEBUG  "` works fine).

> **Note:** this env var is only read the *first* time `get_logger()`
> is called anywhere in the process. Changing `os.environ` afterward
> has no effect — use `set_level()` instead (below) if you need to
> change verbosity while the program is already running.

### At runtime, programmatically

```python
logger = get_logger()

logger.info("this is suppressed at the default warning level")

logger.set_level("debug")

logger.debug("this now appears")
```

This is useful for things like temporarily raising verbosity around a
specific operation you're debugging, or toggling based on a runtime
flag / admin command rather than an env var.

## Setting the service ID

By default, every log line's `service_id` is `"cybergenesis"`. Override
it with an environment variable — useful when multiple services share
this same logging code and you want to tell their output apart:

```bash
export CYBERGENESIS_SERVICE_ID=payments-api
```

```json
{"service_id": "payments-api", ...}
```

Unlike the log level, this one *is* re-read on every single log call,
so it can change during the process lifetime if needed (e.g. via
`os.environ["CYBERGENESIS_SERVICE_ID"] = "..."`).

## Guaranteed fields

Every log line always includes these four fields, regardless of what
extra kwargs you pass:

| Field | Description |
|---|---|
| `service_id` | From `CYBERGENESIS_SERVICE_ID`, defaults to `"cybergenesis"` |
| `log_id` | A fresh random UUID4, unique per log call |
| `level` | One of `debug`, `info`, `warning`, `error`, `critical` |
| `message` | The message string you passed |

## Output destination

Logs are written to **stdout**, not stderr or a file — this is the
standard convention for containerized services, so your orchestrator
(Docker, Kubernetes, etc.) or a log-shipping sidecar (Filebeat,
Fluent Bit, Vector, ...) can tail stdout and forward each JSON line
downstream (e.g. into Kafka) with zero custom parsing.

## Environment variables reference

| Variable | Purpose | Default |
|---|---|---|
| `CYBERGENESIS_LOG` | Log level threshold | `warning` |
| `CYBERGENESIS_SERVICE_ID` | Value of the `service_id` field | `cybergenesis` |

## Full example

```python
from logger import get_logger

logger = get_logger()

logger.info("user logged in", user_id=42, ip="10.0.0.1")
logger.warning("rate limit approaching", user_id=42, remaining=5)

logger.set_level("debug")

logger.error("payment failed", order_id="ord_123", reason="card_declined")
logger.debug("cache miss", key="session:42")
```

```bash
CYBERGENESIS_SERVICE_ID=payments-api PYTHONPATH=src python3 example.py
```

```json
{"service_id": "payments-api", "log_id": "...", "level": "warning", "message": "rate limit approaching", "user_id": 42, "remaining": 5}
{"service_id": "payments-api", "log_id": "...", "level": "error", "message": "payment failed", "order_id": "ord_123", "reason": "card_declined"}
{"service_id": "payments-api", "log_id": "...", "level": "debug", "message": "cache miss", "key": "session:42"}
```

(`info` is missing because the level was still `warning` at that
point in the script.)

## Testing

Run the test suite with coverage:

```bash
PYTHONPATH=src pytest --cov=logger --cov-report=term-missing test/
```

If you're writing tests that use this logger, call
`StructuredLogger.reset_for_tests_only()` in a fixture between tests
to reset its internal singleton/handler state — otherwise state from
one test can leak into the next.