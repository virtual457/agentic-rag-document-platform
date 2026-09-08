from __future__ import annotations

import logging
import sys

import structlog

from src.config import get_settings

_INITIALIZED = False


def _init_once() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=level,
    )
    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.enable_structured_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
    _INITIALIZED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    _init_once()
    return structlog.get_logger(name)
