"""Billing repositories.

These repositories expose user-scoped reads by default. Provider-ID lookups are
reserved for future signed webhook/application internals.
"""

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.billing import ProviderEventClaim
from backend.models.billing import (
    BillingAuditLog,
    BillingPlan,
    BillingPrice,
    PaymentCheckoutSession,
    PaymentProviderEvent,
    PaymentTransaction,
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
            .options(
                selectinload(BillingPlan.prices),
                selectinload(BillingPlan.entitlements),
            )
            .where(BillingPlan.is_active.is_(True))
            .order_by(BillingPlan.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_plan_by_code(self, code: str) -> BillingPlan | None:
        result = await self._session.execute(
            select(BillingPlan)
            .options(
                selectinload(BillingPlan.prices),
                selectinload(BillingPlan.entitlements),
            )
            .where(BillingPlan.code == code)
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
            .options(
                selectinload(UserSubscription.plan).selectinload(
                    BillingPlan.entitlements
                )
            )
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(self._CURRENT_STATUSES),
            )
            .order_by(UserSubscription.created_at.desc())
        )
        return result.scalars().first()

    async def lock_current_for_user(self, user_id: UUID) -> UserSubscription | None:
        result = await self._session.execute(
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(self._CURRENT_STATUSES),
            )
            .order_by(UserSubscription.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        return result.scalar_one_or_none()

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

    async def create_active(
        self,
        user_id: UUID,
        plan_id: UUID,
        provider: str,
        current_period_start: datetime,
        current_period_end: datetime,
    ) -> UserSubscription:
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            provider=provider,
            status="active",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=False,
            renewal_retry_count=0,
        )
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def update_active_period(
        self,
        subscription_id: UUID,
        plan_id: UUID,
        provider: str,
        current_period_start: datetime,
        current_period_end: datetime,
    ) -> UserSubscription | None:
        await self._session.execute(
            update(UserSubscription)
            .where(UserSubscription.id == subscription_id)
            .values(
                plan_id=plan_id,
                provider=provider,
                status="active",
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                cancel_at_period_end=False,
                canceled_at=None,
                last_failure_reason=None,
                renewal_retry_count=0,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        result = await self._session.execute(
            select(UserSubscription).where(UserSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()


class UsageEventRepository:
    """Append-only usage event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def acquire_period_lock(
        self,
        user_id: UUID,
        feature_code: str,
        period_start: datetime,
    ) -> None:
        """Acquire a PostgreSQL transaction advisory lock for quota accounting."""
        lock_input = f"{user_id}:{feature_code}:{period_start.isoformat()}".encode()
        lock_bytes = hashlib.blake2b(lock_input, digest_size=8).digest()
        unsigned_key = int.from_bytes(lock_bytes, byteorder="big", signed=False)
        signed_key = unsigned_key - (1 << 64) if unsigned_key >= (1 << 63) else unsigned_key
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": signed_key},
        )

    async def get_by_idempotency_key(
        self,
        user_id: UUID,
        feature_code: str,
        idempotency_key: str,
    ) -> UsageEvent | None:
        result = await self._session.execute(
            select(UsageEvent).where(
                UsageEvent.user_id == user_id,
                UsageEvent.feature_code == feature_code,
                UsageEvent.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def count_for_period(
        self,
        user_id: UUID,
        feature_code: str,
        period_start: datetime,
        period_end: datetime,
        statuses: list[str],
    ) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(UsageEvent.quantity), 0)).where(
                UsageEvent.user_id == user_id,
                UsageEvent.feature_code == feature_code,
                UsageEvent.period_start == period_start,
                UsageEvent.period_end == period_end,
                UsageEvent.status.in_(statuses),
            )
        )
        return int(result.scalar_one())

    async def summary_for_period(
        self,
        user_id: UUID,
        period_start: datetime,
        period_end: datetime,
        statuses: list[str],
    ) -> dict[str, int]:
        result = await self._session.execute(
            select(
                UsageEvent.feature_code,
                func.coalesce(func.sum(UsageEvent.quantity), 0),
            )
            .where(
                UsageEvent.user_id == user_id,
                UsageEvent.period_start == period_start,
                UsageEvent.period_end == period_end,
                UsageEvent.status.in_(statuses),
            )
            .group_by(UsageEvent.feature_code)
        )
        return {feature: int(total) for feature, total in result.all()}

    async def create(
        self,
        user_id: UUID,
        feature_code: str,
        operation: str,
        quantity: int,
        status: str,
        idempotency_key: str | None = None,
        subscription_id: UUID | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
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
            period_start=period_start,
            period_end=period_end,
            status=status,
            idempotency_key=idempotency_key,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def update_status(
        self,
        event_id: UUID,
        status: str,
    ) -> UsageEvent | None:
        await self._session.execute(
            update(UsageEvent).where(UsageEvent.id == event_id).values(status=status)
        )
        await self._session.flush()
        result = await self._session.execute(
            select(UsageEvent).where(UsageEvent.id == event_id)
        )
        return result.scalar_one_or_none()


class PaymentEventRepository:
    """Data access for sanitized provider events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim_provider_event(
        self,
        provider: str,
        provider_event_id: str,
        event_type: str,
        payload_hash: str,
        provider_payment_id: str | None = None,
        provider_subscription_id: str | None = None,
        provider_status: str | None = None,
    ) -> ProviderEventClaim:
        """Atomically insert a provider event or return the existing duplicate."""
        stmt = (
            insert(PaymentProviderEvent)
            .values(
                provider=provider,
                provider_event_id=provider_event_id,
                event_type=event_type,
                provider_payment_id=provider_payment_id,
                provider_subscription_id=provider_subscription_id,
                provider_status=provider_status,
                payload_hash=payload_hash,
                processing_status="received",
            )
            .on_conflict_do_nothing(
                constraint="uq_payment_provider_event_provider_event"
            )
            .returning(PaymentProviderEvent)
        )
        result = await self._session.execute(stmt)
        event = result.scalar_one_or_none()
        if event is not None:
            return ProviderEventClaim(
                event_id=event.id,
                is_duplicate=False,
                processing_status=str(event.processing_status),
            )

        existing = await self.get_by_provider_event_id(provider, provider_event_id)
        if existing is None:
            raise RuntimeError("Provider event claim failed without existing row")
        return ProviderEventClaim(
            event_id=existing.id,
            is_duplicate=True,
            processing_status=str(existing.processing_status),
        )

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

    async def payload_matches(
        self,
        event_id: UUID,
        payload_hash: str,
        provider_payment_id: str | None = None,
        provider_subscription_id: str | None = None,
        provider_status: str | None = None,
    ) -> bool:
        result = await self._session.execute(
            select(PaymentProviderEvent).where(PaymentProviderEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            return False
        return (
            event.payload_hash == payload_hash
            and event.provider_payment_id == provider_payment_id
            and event.provider_subscription_id == provider_subscription_id
            and event.provider_status == provider_status
        )

    async def mark_processed(self, event_id: UUID) -> PaymentProviderEvent | None:
        return await self._update_processing_status(event_id, "processed")

    async def mark_ignored(
        self,
        event_id: UUID,
        reason: str | None = None,
    ) -> PaymentProviderEvent | None:
        return await self._update_processing_status(event_id, "ignored", reason)

    async def mark_failed(
        self,
        event_id: UUID,
        error: str,
    ) -> PaymentProviderEvent | None:
        return await self._update_processing_status(event_id, "failed", error)

    async def _update_processing_status(
        self,
        event_id: UUID,
        status: str,
        message: str | None = None,
    ) -> PaymentProviderEvent | None:
        await self._session.execute(
            update(PaymentProviderEvent)
            .where(PaymentProviderEvent.id == event_id)
            .values(
                processing_status=status,
                error=message,
                processed_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        result = await self._session.execute(
            select(PaymentProviderEvent).where(PaymentProviderEvent.id == event_id)
        )
        return result.scalar_one_or_none()


class PaymentCheckoutSessionRepository:
    """Data access for backend-created checkout references."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        plan_id: UUID,
        price_id: UUID,
        provider: str,
        provider_session_id: str,
        status: str,
        provider_order_id: str | None = None,
        payment_url: str | None = None,
        idempotency_key: str | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
        expires_at: datetime | None = None,
    ) -> PaymentCheckoutSession:
        session = PaymentCheckoutSession(
            user_id=user_id,
            plan_id=plan_id,
            price_id=price_id,
            provider=provider,
            provider_session_id=provider_session_id,
            provider_order_id=provider_order_id,
            payment_url=payment_url,
            idempotency_key=idempotency_key,
            status=status,
            success_url=success_url,
            cancel_url=cancel_url,
            expires_at=expires_at,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def find_reusable(
        self,
        user_id: UUID,
        plan_id: UUID,
        price_id: UUID,
        provider: str,
        at: datetime,
    ) -> PaymentCheckoutSession | None:
        result = await self._session.execute(
            select(PaymentCheckoutSession)
            .where(
                PaymentCheckoutSession.user_id == user_id,
                PaymentCheckoutSession.plan_id == plan_id,
                PaymentCheckoutSession.price_id == price_id,
                PaymentCheckoutSession.provider == provider,
                PaymentCheckoutSession.status.in_(("created", "redirected")),
                PaymentCheckoutSession.payment_url.is_not(None),
                or_(
                    PaymentCheckoutSession.expires_at.is_(None),
                    PaymentCheckoutSession.expires_at > at,
                ),
            )
            .order_by(desc(PaymentCheckoutSession.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        checkout_session_id: UUID,
        status: str,
        completed_at: datetime | None = None,
    ) -> PaymentCheckoutSession | None:
        values = {"status": status}
        if completed_at is not None:
            values["completed_at"] = completed_at
        await self._session.execute(
            update(PaymentCheckoutSession)
            .where(PaymentCheckoutSession.id == checkout_session_id)
            .values(**values)
        )
        await self._session.flush()
        result = await self._session.execute(
            select(PaymentCheckoutSession).where(
                PaymentCheckoutSession.id == checkout_session_id
            )
        )
        return result.scalar_one_or_none()


class PaymentTransactionRepository:
    """Data access for provider payment attempts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        checkout_session_id: UUID,
        provider: str,
        provider_payment_id: str,
        amount_minor: int,
        currency: str,
        status: str,
        provider_status: str | None = None,
    ) -> PaymentTransaction:
        transaction = PaymentTransaction(
            user_id=user_id,
            checkout_session_id=checkout_session_id,
            provider=provider,
            provider_payment_id=provider_payment_id,
            provider_status=provider_status,
            amount_minor=amount_minor,
            currency=currency,
            status=status,
        )
        self._session.add(transaction)
        await self._session.flush()
        return transaction

    async def get_with_checkout_by_provider_payment_id(
        self,
        provider: str,
        provider_payment_id: str,
    ) -> tuple[PaymentTransaction, PaymentCheckoutSession, BillingPrice] | None:
        result = await self._session.execute(
            select(PaymentTransaction, PaymentCheckoutSession, BillingPrice)
            .join(
                PaymentCheckoutSession,
                PaymentTransaction.checkout_session_id == PaymentCheckoutSession.id,
            )
            .join(BillingPrice, PaymentCheckoutSession.price_id == BillingPrice.id)
            .where(
                PaymentTransaction.provider == provider,
                PaymentTransaction.provider_payment_id == provider_payment_id,
            )
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1], row[2]

    async def update_status(
        self,
        transaction_id: UUID,
        status: str,
        provider_status: str | None = None,
        paid_at: datetime | None = None,
        refunded_at: datetime | None = None,
        failure_reason: str | None = None,
        subscription_id: UUID | None = None,
    ) -> PaymentTransaction | None:
        values = {
            "status": status,
            "provider_status": provider_status,
            "failure_reason": failure_reason,
            "updated_at": datetime.now(timezone.utc),
        }
        if subscription_id is not None:
            values["subscription_id"] = subscription_id
        if paid_at is not None:
            values["paid_at"] = paid_at
        if refunded_at is not None:
            values["refunded_at"] = refunded_at
        await self._session.execute(
            update(PaymentTransaction)
            .where(PaymentTransaction.id == transaction_id)
            .values(**values)
        )
        await self._session.flush()
        result = await self._session.execute(
            select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()


class BillingAuditLogRepository:
    """Data access for sanitized billing audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        action: str,
        actor_type: str,
        user_id: UUID | None = None,
        subscription_id: UUID | None = None,
        payment_transaction_id: UUID | None = None,
        payment_provider_event_id: UUID | None = None,
        old_status: str | None = None,
        new_status: str | None = None,
        reason: str | None = None,
        metadata: dict | None = None,
    ) -> BillingAuditLog:
        event = BillingAuditLog(
            user_id=user_id,
            subscription_id=subscription_id,
            payment_transaction_id=payment_transaction_id,
            payment_provider_event_id=payment_provider_event_id,
            actor_type=actor_type,
            action=action,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            metadata_json=metadata or {},
        )
        self._session.add(event)
        await self._session.flush()
        return event
