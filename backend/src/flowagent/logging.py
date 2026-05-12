"""Structured logging via structlog.

Provides a single :func:`configure_logging` entrypoint that should be called
exactly once at application start (CLI entrypoint, FastAPI ``startup`` hook,
or test fixture). Once configured, every module can grab a logger with::

    log = structlog.get_logger(__name__)
    log.info("event_name", key=value)

Output format:

* When ``log_json`` is False (default in dev): pretty key-value renderer.
* When ``log_json`` is True (production / containers): JSON one line per event.
"""

from __future__ import annotations

import logging
import sys
from typing import cast

import structlog


def configure_logging(*, level: str = "INFO", json_output: bool = False) -> None:
    """Set up structlog and the stdlib root logger.

    Safe to call multiple times — calls past the first are no-ops as long as
    the arguments match. Mismatched re-configuration replaces the previous
    setup, which is useful in tests.
    """
    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unknown log level: {level!r}")

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
        force=True,
    )

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound logger. Thin wrapper for import ergonomics."""
    return cast("structlog.stdlib.BoundLogger", structlog.get_logger(name))


__all__ = ["configure_logging", "get_logger"]
