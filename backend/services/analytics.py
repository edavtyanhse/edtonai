"""Analytics service - accepts behavior events into application logs."""

import logging
from datetime import UTC, datetime
from json import dumps
from typing import Any

from backend.domain.analytics import AnalyticsEventAccepted

logger = logging.getLogger(__name__)


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
                    "properties": properties or {},
                    "user_email": user_email,
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
