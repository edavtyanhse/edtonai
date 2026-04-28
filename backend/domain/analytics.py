"""Analytics domain DTOs."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnalyticsEventAccepted:
    """Result of accepting an analytics event."""

    status: str
    event_name: str
    session_id: str
    logged_at: datetime
