"""Billing request schemas."""

from pydantic import BaseModel, Field


class CreateCheckoutSessionRequest(BaseModel):
    """User request to start hosted checkout for a server-owned plan."""

    plan_code: str = Field(..., min_length=1, max_length=64)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=255)
