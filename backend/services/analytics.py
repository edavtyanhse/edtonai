"""Analytics service - accepts behavior events into application logs."""

import hashlib
import logging
from datetime import UTC, datetime
from json import dumps
from typing import Any

from backend.domain.analytics import AnalyticsEventAccepted

logger = logging.getLogger(__name__)

_SENSITIVE_PROPERTY_KEYS = {
    "authorization",
    "cookie",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "resume_text",
    "vacancy_text",
    "result_text",
    "payment_token",
}


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode("utf-8")).hexdigest()


def _safe_properties(properties: dict[str, Any] | None) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in (properties or {}).items():
        normalized_key = key.lower()
        if any(sensitive in normalized_key for sensitive in _SENSITIVE_PROPERTY_KEYS):
            safe[key] = "[REDACTED]"
            continue
        if isinstance(value, str):
            safe[key] = value[:256]
        elif isinstance(value, (int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)[:256]
    return safe


class AnalyticsService:
    """Application service for behavior analytics ingestion."""

    async def ingest_event(
        self,
        user_email: str,
        event_name: str,
        session_id: str,
        step: str | None = None,
        ui_variant: str | None = None,
        user_segment: str | None = None,
        occurred_at: datetime | None = None,
        properties: dict[str, Any] | None = None,
    ) -> AnalyticsEventAccepted:
        """Write an authenticated behavior event to structured logs."""
        logged_at = datetime.now(UTC)
        logger.info(
            "ANALYTICS_EVENT %s",
            dumps(
                {
                    "event_name": event_name,
                    "session_id": session_id,
                    "step": step,
                    "ui_variant": ui_variant,
                    "user_segment": user_segment,
                    "occurred_at": occurred_at.isoformat() if occurred_at else None,
                    "properties": _safe_properties(properties),
                    "user_hash": _hash_email(user_email),
                },
                ensure_ascii=False,
            ),
        )
        return AnalyticsEventAccepted(
            status="accepted",
            event_name=event_name,
            session_id=session_id,
            logged_at=logged_at,
        )
