"""Billing response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class BillingPriceResponse(BaseModel):
    """Public price data controlled by the backend."""

    provider: str
    amount_minor: int
    currency: str = Field(..., min_length=3, max_length=3)
    billing_period: str


class PlanEntitlementResponse(BaseModel):
    """Public plan entitlement data."""

    feature_code: str
    limit_value: int | None = None
    reset_period: str | None = None


class BillingPlanResponse(BaseModel):
    """Public active billing plan."""

    code: str
    title: str
    description: str | None = None
    billing_period: str
    trial_days: int
    prices: list[BillingPriceResponse]
    entitlements: list[PlanEntitlementResponse]


class BillingPlanListResponse(BaseModel):
    """List of active billing plans."""

    items: list[BillingPlanResponse]


class CurrentSubscriptionResponse(BaseModel):
    """Current user subscription state without provider identifiers."""

    status: str
    plan_code: str | None = None
    trial_end: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool


class UsageFeatureResponse(BaseModel):
    """Current usage summary for a billable feature."""

    feature_code: str
    used: int
    limit_value: int | None = None
    remaining: int | None = None
    period_start: datetime
    period_end: datetime


class BillingAccountResponse(BaseModel):
    """Current billing account state for the authenticated user."""

    subscription: CurrentSubscriptionResponse | None = None
    usage: list[UsageFeatureResponse]
