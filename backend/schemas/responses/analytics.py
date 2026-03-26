"""Analytics event response schemas."""

from datetime import datetime

from pydantic import BaseModel


class AnalyticsEventAcceptedResponse(BaseModel):
    """Response after analytics event is accepted for logging."""

    status: str
    event_name: str
    session_id: str
    logged_at: datetime
