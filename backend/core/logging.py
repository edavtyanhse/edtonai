"""Logging configuration with request_id support."""

import logging
import re
import sys
from contextvars import ContextVar
from typing import Any

from backend.core.config import settings

# Context variable for request tracing
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Inject request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


_SENSITIVE_PATTERNS = (
    re.compile(r"(Authorization:\s*Bearer\s+)[^\s,;]+", re.IGNORECASE),
    re.compile(r"(refresh_token=)[^&\s]+", re.IGNORECASE),
    re.compile(r"(access_token=)[^&\s]+", re.IGNORECASE),
    re.compile(r"(Cookie:\s*)[^,\n]+", re.IGNORECASE),
    re.compile(r"(Set-Cookie:\s*)[^,\n]+", re.IGNORECASE),
)


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _redact_value(item) for key, item in value.items()}
    return value


class SensitiveDataFilter(logging.Filter):
    """Redact common token/cookie values from application logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact_text(record.msg)
        if record.args:
            record.args = _redact_value(record.args)
        return True


def setup_logging() -> None:
    """Configure application logging."""
    fmt = "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    handler.addFilter(RequestIdFilter())
    handler.addFilter(SensitiveDataFilter())

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()
    root.addHandler(handler)
