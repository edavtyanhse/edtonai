"""Pure billing domain objects used by application services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

AI_OPERATION_FEATURE = "ai_operation"
TEMPORARY_HIGH_FREE_QUOTA_LIMIT = 10_000


class SubscriptionStatus(StrEnum):
    """Internal server-authoritative subscription states."""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELED = "canceled"


class PaymentStatus(StrEnum):
    """Internal provider-agnostic payment transaction states."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    PARTIALLY_CANCELED = "partially_canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CHARGEBACK = "chargeback"
    UNKNOWN = "unknown"


class CheckoutSessionStatus(StrEnum):
    """Internal hosted checkout reference states."""

    CREATED = "created"
    REDIRECTED = "redirected"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELED = "canceled"


class ProviderEventProcessingStatus(StrEnum):
    """Internal webhook/event journal states."""

    RECEIVED = "received"
    PROCESSED = "processed"
    IGNORED = "ignored"
    FAILED = "failed"


GRANTING_SUBSCRIPTION_STATUSES = frozenset(
    {
        SubscriptionStatus.TRIALING.value,
        SubscriptionStatus.ACTIVE.value,
    }
)
CURRENT_SUBSCRIPTION_STATUSES = frozenset(
    {
        SubscriptionStatus.TRIALING.value,
        SubscriptionStatus.ACTIVE.value,
        SubscriptionStatus.PAST_DUE.value,
        SubscriptionStatus.PAUSED.value,
    }
)
TERMINAL_SUBSCRIPTION_STATUSES = frozenset(
    {
        SubscriptionStatus.EXPIRED.value,
        SubscriptionStatus.CANCELED.value,
    }
)

TBANK_PAYMENT_STATUS_MAP: dict[str, PaymentStatus] = {
    "NEW": PaymentStatus.PENDING,
    "FORM_SHOWED": PaymentStatus.PENDING,
    "DEADLINE_EXPIRED": PaymentStatus.FAILED,
    "AUTHORIZED": PaymentStatus.AUTHORIZED,
    "AUTH_FAIL": PaymentStatus.FAILED,
    "REJECTED": PaymentStatus.FAILED,
    "CONFIRMED": PaymentStatus.SUCCEEDED,
    "CANCELED": PaymentStatus.CANCELED,
    "REVERSED": PaymentStatus.CANCELED,
    "PARTIAL_REVERSED": PaymentStatus.PARTIALLY_CANCELED,
    "REFUNDED": PaymentStatus.REFUNDED,
    "PARTIAL_REFUNDED": PaymentStatus.PARTIALLY_REFUNDED,
}


def normalize_tbank_payment_status(raw_status: str | None) -> PaymentStatus:
    """Map a raw T-Bank acquiring status to the internal payment state."""
    if not raw_status:
        return PaymentStatus.UNKNOWN
    return TBANK_PAYMENT_STATUS_MAP.get(raw_status.strip().upper(), PaymentStatus.UNKNOWN)


def is_subscription_transition_allowed(current: str, target: str) -> bool:
    """Return whether a subscription status transition is valid."""
    transitions = {
        SubscriptionStatus.TRIALING.value: {
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.PAST_DUE.value,
            SubscriptionStatus.PAUSED.value,
            SubscriptionStatus.EXPIRED.value,
            SubscriptionStatus.CANCELED.value,
        },
        SubscriptionStatus.ACTIVE.value: {
            SubscriptionStatus.PAST_DUE.value,
            SubscriptionStatus.PAUSED.value,
            SubscriptionStatus.EXPIRED.value,
            SubscriptionStatus.CANCELED.value,
        },
        SubscriptionStatus.PAST_DUE.value: {
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.PAUSED.value,
            SubscriptionStatus.EXPIRED.value,
            SubscriptionStatus.CANCELED.value,
        },
        SubscriptionStatus.PAUSED.value: {
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.EXPIRED.value,
            SubscriptionStatus.CANCELED.value,
        },
        SubscriptionStatus.EXPIRED.value: set(),
        SubscriptionStatus.CANCELED.value: set(),
    }
    if current == target:
        return True
    return target in transitions.get(current, set())


@dataclass(frozen=True)
class EntitlementDecision:
    """Result of a server-side entitlement check."""

    allowed: bool
    feature_code: str
    reason: str
    limit_value: int | None = None
    reset_period: str | None = None
    used: int = 0
    remaining: int | None = None
    plan_code: str | None = None
    subscription_id: UUID | None = None
    subscription_status: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


@dataclass(frozen=True)
class UsageReservation:
    """Reserved usage event to be committed or canceled after work finishes."""

    event_id: UUID
    user_id: UUID
    feature_code: str
    operation: str
    idempotency_key: str
    status: str
    provider_call_allowed: bool


@dataclass(frozen=True)
class CheckoutSessionRequest:
    """Provider checkout request built only from server-controlled data."""

    user_id: UUID
    plan_code: str
    amount_minor: int
    currency: str
    success_url: str
    cancel_url: str
    provider_price_id: str | None = None


@dataclass(frozen=True)
class CheckoutSessionResult:
    """Provider checkout response without cardholder data."""

    provider: str
    provider_session_id: str
    payment_url: str | None
    status: str
    expires_at: datetime | None = None
    provider_status: str | None = None
    can_activate_entitlement: bool = False


@dataclass(frozen=True)
class ProviderWebhookEvent:
    """Sanitized provider event passed into application services."""

    provider: str
    provider_event_id: str
    event_type: str
    payload_hash: str
    provider_payment_id: str | None = None
    provider_subscription_id: str | None = None
    provider_status: str | None = None


@dataclass(frozen=True)
class ProviderEventClaim:
    """Result of atomically claiming a provider event for processing."""

    event_id: UUID
    is_duplicate: bool
    processing_status: str


@dataclass(frozen=True)
class BillingPriceView:
    """Safe public price data without provider-internal IDs."""

    provider: str
    amount_minor: int
    currency: str
    billing_period: str


@dataclass(frozen=True)
class PlanEntitlementView:
    """Safe public entitlement data."""

    feature_code: str
    limit_value: int | None
    reset_period: str | None


@dataclass(frozen=True)
class BillingPlanView:
    """Safe public plan data."""

    code: str
    title: str
    description: str | None
    billing_period: str
    trial_days: int
    prices: list[BillingPriceView]
    entitlements: list[PlanEntitlementView]


@dataclass(frozen=True)
class SubscriptionView:
    """User-facing subscription state without provider identifiers."""

    status: str
    plan_code: str | None
    trial_end: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool


@dataclass(frozen=True)
class UsageView:
    """User-facing usage state for a feature and period."""

    feature_code: str
    used: int
    limit_value: int | None
    remaining: int | None
    period_start: datetime
    period_end: datetime


@dataclass(frozen=True)
class BillingAccountView:
    """Current billing/account summary for the authenticated user."""

    subscription: SubscriptionView | None
    usage: list[UsageView]
