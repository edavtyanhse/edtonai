"""Billing repositories.

These repositories expose user-scoped reads by default. Provider-ID lookups are
reserved for future signed webhook/application internals.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.billing import (
    BillingPlan,
    BillingPrice,
    PaymentProviderEvent,
    UsageEvent,
    UserSubscription,
)


class BillingPlanRepository:
    """Data access for backend-controlled plans, prices and entitlements."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_plans(self) -> list[BillingPlan]:
        result = await self._session.execute(
            select(BillingPlan)
            .where(BillingPlan.is_active.is_(True))
            .order_by(BillingPlan.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_plan_by_code(self, code: str) -> BillingPlan | None:
        result = await self._session.execute(
            select(BillingPlan).where(BillingPlan.code == code)
        )
        return result.scalar_one_or_none()

    async def get_active_price(
        self,
        plan_code: str,
        provider: str,
    ) -> BillingPrice | None:
        result = await self._session.execute(
            select(BillingPrice)
            .join(BillingPlan, BillingPrice.plan_id == BillingPlan.id)
            .where(
                BillingPlan.code == plan_code,
                BillingPlan.is_active.is_(True),
                BillingPrice.provider == provider,
                BillingPrice.is_active.is_(True),
            )
            .order_by(BillingPrice.created_at.desc())
        )
        return result.scalars().first()


class SubscriptionRepository:
    """Data access for subscription state."""

    _CURRENT_STATUSES = {"trialing", "active", "past_due", "paused"}

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_for_user(self, user_id: UUID) -> UserSubscription | None:
        result = await self._session.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(self._CURRENT_STATUSES),
            )
            .order_by(UserSubscription.created_at.desc())
        )
        return result.scalars().first()

    async def get_by_provider_subscription_id(
        self,
        provider: str,
        provider_subscription_id: str,
    ) -> UserSubscription | None:
        result = await self._session.execute(
            select(UserSubscription).where(
                UserSubscription.provider == provider,
                UserSubscription.provider_subscription_id == provider_subscription_id,
            )
        )
        return result.scalar_one_or_none()


class UsageEventRepository:
    """Append-only usage event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        feature_code: str,
        operation: str,
        quantity: int,
        status: str,
        idempotency_key: str | None = None,
        subscription_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict | None = None,
    ) -> UsageEvent:
        event = UsageEvent(
            user_id=user_id,
            subscription_id=subscription_id,
            feature_code=feature_code,
            operation=operation,
            quantity=quantity,
            status=status,
            idempotency_key=idempotency_key,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self._session.add(event)
        await self._session.flush()
        return event


class PaymentEventRepository:
    """Data access for sanitized provider events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider_event_id(
        self,
        provider: str,
        provider_event_id: str,
    ) -> PaymentProviderEvent | None:
        result = await self._session.execute(
            select(PaymentProviderEvent).where(
                PaymentProviderEvent.provider == provider,
                PaymentProviderEvent.provider_event_id == provider_event_id,
            )
        )
        return result.scalar_one_or_none()
