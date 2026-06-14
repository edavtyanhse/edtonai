"""Billing, entitlement and usage application services."""

from __future__ import annotations

from calendar import monthrange
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID

from backend.core.config import Settings
from backend.domain.billing import (
    AI_OPERATION_FEATURE,
    CURRENT_SUBSCRIPTION_STATUSES,
    GRANTING_SUBSCRIPTION_STATUSES,
    BillingAccountView,
    BillingPlanView,
    BillingPriceView,
    CheckoutSessionRequest,
    CheckoutSessionResult,
    CheckoutSessionStatus,
    EntitlementDecision,
    PaymentStatus,
    PlanEntitlementView,
    ProviderWebhookEvent,
    SubscriptionStatus,
    SubscriptionView,
    UsageReservation,
    UsageView,
    is_subscription_transition_allowed,
    normalize_tbank_payment_status,
)
from backend.errors.business import EntitlementDeniedError
from backend.integration.payments.base import (
    PaymentProviderClient,
    PaymentProviderDisabledError,
)
from backend.repositories.interfaces import (
    IBillingAuditLogRepository,
    IBillingPlanRepository,
    IPaymentCheckoutSessionRepository,
    IPaymentEventRepository,
    IPaymentTransactionRepository,
    ISubscriptionRepository,
    IUsageEventRepository,
)

_COUNTED_USAGE_STATUSES = ["reserved", "committed"]
_PAID_PERIOD_MONTHS = {
    "month": 1,
    "quarter": 3,
}
_FINAL_FAILED_PAYMENT_STATUSES = {
    PaymentStatus.FAILED,
    PaymentStatus.CANCELED,
    PaymentStatus.PARTIALLY_CANCELED,
}
_REVERSAL_PAYMENT_STATUSES = {
    PaymentStatus.REFUNDED,
    PaymentStatus.PARTIALLY_REFUNDED,
    PaymentStatus.CHARGEBACK,
}
_PAYMENT_STATUS_RANK = {
    PaymentStatus.UNKNOWN: 0,
    PaymentStatus.PENDING: 10,
    PaymentStatus.AUTHORIZED: 20,
    PaymentStatus.SUCCEEDED: 30,
    PaymentStatus.FAILED: 30,
    PaymentStatus.CANCELED: 30,
    PaymentStatus.PARTIALLY_CANCELED: 30,
    PaymentStatus.PARTIALLY_REFUNDED: 40,
    PaymentStatus.REFUNDED: 40,
    PaymentStatus.CHARGEBACK: 50,
}


def _to_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(value)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_stale_payment_status(
    current_status: PaymentStatus,
    incoming_status: PaymentStatus,
) -> bool:
    if current_status == incoming_status:
        return False
    if current_status in _REVERSAL_PAYMENT_STATUSES:
        return True
    if current_status in _FINAL_FAILED_PAYMENT_STATUSES:
        return True
    if current_status == PaymentStatus.SUCCEEDED:
        return incoming_status not in _REVERSAL_PAYMENT_STATUSES
    return _PAYMENT_STATUS_RANK[incoming_status] < _PAYMENT_STATUS_RANK[current_status]


def _add_billing_period(start: datetime, billing_period: str) -> datetime:
    period = billing_period.strip().lower()
    if period == "week":
        return start + timedelta(days=7)
    months = _PAID_PERIOD_MONTHS.get(period)
    if months is None:
        raise ValueError(f"Unsupported billing period: {billing_period}")
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


def _calendar_month_window(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


class EntitlementService:
    """Server-authoritative entitlement decisions for billable features."""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        settings: Settings,
    ) -> None:
        self._subscription_repo = subscription_repo
        self._settings = settings

    async def check_feature(
        self,
        user_id: str | UUID,
        feature_code: str,
        operation: str | None = None,
        at: datetime | None = None,
    ) -> EntitlementDecision:
        """Return whether a user may use a feature before usage counting."""
        now = at or _utcnow()
        user_uuid = _to_uuid(user_id)
        subscription = await self._subscription_repo.get_current_for_user(user_uuid)
        period_start, period_end = _calendar_month_window(now)

        if subscription is None:
            return EntitlementDecision(
                allowed=True,
                feature_code=feature_code,
                reason="free_quota",
                limit_value=self._settings.ai_monthly_free_quota,
                reset_period="month",
                plan_code="free",
                period_start=period_start,
                period_end=period_end,
            )

        status = str(subscription.status)
        plan = getattr(subscription, "plan", None)
        plan_code = getattr(plan, "code", None)

        if status not in GRANTING_SUBSCRIPTION_STATUSES:
            return self._deny(
                feature_code,
                reason=f"subscription_{status}",
                plan_code=plan_code,
                subscription=subscription,
            )

        if status == "trialing":
            trial_end = subscription.trial_end
            if trial_end is None or trial_end <= now:
                return self._deny(
                    feature_code,
                    reason="trial_expired",
                    plan_code=plan_code,
                    subscription=subscription,
                )
            period_start = subscription.trial_start or period_start
            period_end = trial_end

        if status == "active":
            current_period_end = subscription.current_period_end
            if current_period_end is None or current_period_end <= now:
                return self._deny(
                    feature_code,
                    reason="subscription_period_expired",
                    plan_code=plan_code,
                    subscription=subscription,
                )
            period_start = subscription.current_period_start or period_start
            period_end = current_period_end

        entitlement = self._find_entitlement(
            entitlements=list(getattr(plan, "entitlements", []) or []),
            feature_code=feature_code,
            operation=operation,
        )
        if entitlement is None:
            return self._deny(
                feature_code,
                reason="feature_not_in_plan",
                plan_code=plan_code,
                subscription=subscription,
            )

        return EntitlementDecision(
            allowed=True,
            feature_code=feature_code,
            reason="plan_entitlement",
            limit_value=entitlement.limit_value,
            reset_period=entitlement.reset_period,
            plan_code=plan_code,
            subscription_id=subscription.id,
            subscription_status=status,
            period_start=period_start,
            period_end=period_end,
        )

    @staticmethod
    def _find_entitlement(
        entitlements: list,
        feature_code: str,
        operation: str | None,
    ):
        if operation is not None:
            for entitlement in entitlements:
                if entitlement.feature_code == operation:
                    return entitlement
        for entitlement in entitlements:
            if entitlement.feature_code == feature_code:
                return entitlement
        return None

    @staticmethod
    def _deny(
        feature_code: str,
        reason: str,
        plan_code: str | None,
        subscription,
    ) -> EntitlementDecision:
        return EntitlementDecision(
            allowed=False,
            feature_code=feature_code,
            reason=reason,
            limit_value=0,
            remaining=0,
            plan_code=plan_code,
            subscription_id=subscription.id,
            subscription_status=str(subscription.status),
        )


class UsageService:
    """Reserve, commit and cancel feature usage in a retry-safe way."""

    def __init__(
        self,
        entitlement_service: EntitlementService,
        usage_repo: IUsageEventRepository,
    ) -> None:
        self._entitlement_service = entitlement_service
        self._usage_repo = usage_repo

    async def reserve(
        self,
        user_id: str | UUID,
        feature_code: str,
        operation: str,
        idempotency_key: str,
        quantity: int = 1,
    ) -> UsageReservation:
        """Reserve quota before an expensive operation starts."""
        if not idempotency_key:
            raise EntitlementDeniedError("Billable operation requires idempotency key")
        if quantity <= 0:
            raise ValueError("Usage quantity must be positive")

        user_uuid = _to_uuid(user_id)
        decision = await self._entitlement_service.check_feature(
            user_uuid,
            feature_code,
            operation=operation,
        )
        if not decision.allowed:
            raise EntitlementDeniedError(self._message_for_denial(decision))

        period_start = decision.period_start
        period_end = decision.period_end
        if period_start is None or period_end is None:
            raise EntitlementDeniedError("Subscription period is not available")

        await self._usage_repo.acquire_period_lock(
            user_uuid,
            feature_code,
            period_start,
        )
        existing = await self._usage_repo.get_by_idempotency_key(
            user_uuid,
            feature_code,
            idempotency_key,
        )
        if existing is not None:
            if existing.status in {"reserved", "committed"}:
                return self._to_reservation(
                    existing,
                    user_uuid,
                    feature_code,
                    operation,
                    provider_call_allowed=False,
                )

        limit_value = decision.limit_value
        if limit_value is not None:
            used = await self._usage_repo.count_for_period(
                user_uuid,
                feature_code,
                period_start,
                period_end,
                statuses=_COUNTED_USAGE_STATUSES,
            )
            if used + quantity > limit_value:
                raise EntitlementDeniedError(
                    "Monthly quota exceeded for this operation"
                )

        if existing is not None:
            await self._usage_repo.update_status(existing.id, "reserved")
            return self._to_reservation(
                existing,
                user_uuid,
                feature_code,
                operation,
                provider_call_allowed=True,
                status="reserved",
            )

        event = await self._usage_repo.create(
            user_id=user_uuid,
            subscription_id=decision.subscription_id,
            feature_code=feature_code,
            operation=operation,
            quantity=quantity,
            status="reserved",
            idempotency_key=idempotency_key,
            period_start=period_start,
            period_end=period_end,
        )
        return self._to_reservation(
            event,
            user_uuid,
            feature_code,
            operation,
            provider_call_allowed=True,
        )

    async def commit(self, reservation: UsageReservation) -> None:
        """Mark reserved usage as successfully consumed."""
        await self._usage_repo.update_status(reservation.event_id, "committed")

    async def cancel(self, reservation: UsageReservation, status: str = "failed") -> None:
        """Release reserved usage after failed or canceled work."""
        await self._usage_repo.update_status(reservation.event_id, status)

    @asynccontextmanager
    async def track_ai_call(
        self,
        user_id: str | UUID | None,
        operation: str,
        input_hash: str,
    ) -> AsyncIterator[UsageReservation | None]:
        """Reserve and commit usage around a real AI provider call."""
        if user_id is None:
            yield None
            return

        reservation = await self.reserve(
            user_id=user_id,
            feature_code=AI_OPERATION_FEATURE,
            operation=operation,
            idempotency_key=f"{operation}:{input_hash}",
        )
        if not reservation.provider_call_allowed:
            yield reservation
            return
        try:
            yield reservation
        except Exception:
            await self.cancel(reservation)
            raise
        else:
            await self.commit(reservation)

    @staticmethod
    def _message_for_denial(decision: EntitlementDecision) -> str:
        if decision.reason == "trial_expired":
            return "Trial period has expired"
        if decision.reason == "subscription_period_expired":
            return "Subscription period has expired"
        if decision.reason == "feature_not_in_plan":
            return "Current plan does not include this operation"
        if decision.reason.startswith("subscription_"):
            return "Subscription is not active"
        return "Subscription or quota does not allow this operation"

    @staticmethod
    def _to_reservation(
        event,
        user_id: UUID,
        feature_code: str,
        operation: str,
        provider_call_allowed: bool,
        status: str | None = None,
    ) -> UsageReservation:
        return UsageReservation(
            event_id=event.id,
            user_id=user_id,
            feature_code=feature_code,
            operation=operation,
            idempotency_key=str(event.idempotency_key),
            status=status or str(event.status),
            provider_call_allowed=provider_call_allowed,
        )


class SubscriptionStateMachine:
    """Allowed subscription transitions and period-expiry rules."""

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        return is_subscription_transition_allowed(current, target)

    @staticmethod
    def assert_transition(current: str, target: str) -> None:
        if not is_subscription_transition_allowed(current, target):
            raise ValueError(f"Invalid subscription transition: {current} -> {target}")

    @staticmethod
    def status_after_period_check(subscription, at: datetime | None = None) -> str:
        now = at or _utcnow()
        status = str(subscription.status)
        if status == "trialing" and subscription.trial_end is not None:
            if subscription.trial_end <= now:
                return "expired"
        if status == "active" and subscription.current_period_end is not None:
            if subscription.current_period_end <= now:
                return "expired"
        if status not in CURRENT_SUBSCRIPTION_STATUSES:
            return status
        return status


class PaymentStatusMapper:
    """Provider raw payment status mapping helpers."""

    @staticmethod
    def from_tbank(raw_status: str | None) -> PaymentStatus:
        return normalize_tbank_payment_status(raw_status)


class PaymentWebhookService:
    """Idempotent verified provider webhook processing."""

    def __init__(
        self,
        payment_event_repo: IPaymentEventRepository,
        payment_transaction_repo: IPaymentTransactionRepository,
        checkout_repo: IPaymentCheckoutSessionRepository,
        subscription_repo: ISubscriptionRepository,
        audit_log_repo: IBillingAuditLogRepository,
    ) -> None:
        self._payment_event_repo = payment_event_repo
        self._payment_transaction_repo = payment_transaction_repo
        self._checkout_repo = checkout_repo
        self._subscription_repo = subscription_repo
        self._audit_log_repo = audit_log_repo

    async def process_verified_event(
        self,
        event: ProviderWebhookEvent,
        *,
        signature_verified: bool,
    ):
        """Claim a sanitized event and record a fail-closed processing result."""
        if not signature_verified:
            raise PaymentProviderDisabledError("Payment webhook signature is invalid")

        claim = await self._payment_event_repo.claim_provider_event(
            provider=event.provider,
            provider_event_id=event.provider_event_id,
            event_type=event.event_type,
            provider_payment_id=event.provider_payment_id,
            provider_subscription_id=event.provider_subscription_id,
            provider_status=event.provider_status,
            payload_hash=event.payload_hash,
        )
        if claim.is_duplicate:
            if not await self._payment_event_repo.payload_matches(
                claim.event_id,
                event.payload_hash,
                provider_payment_id=event.provider_payment_id,
                provider_subscription_id=event.provider_subscription_id,
                provider_status=event.provider_status,
            ):
                await self._payment_event_repo.mark_failed(
                    claim.event_id,
                    "duplicate_provider_event_payload_mismatch",
                )
                await self._audit_log_repo.create(
                    action="payment_provider_event_payload_mismatch",
                    actor_type="provider",
                    payment_provider_event_id=claim.event_id,
                    reason="duplicate_provider_event_payload_mismatch",
                    metadata={"provider": event.provider},
                )
                return claim
            await self._audit_log_repo.create(
                action="payment_provider_event_duplicate",
                actor_type="provider",
                payment_provider_event_id=claim.event_id,
                reason="duplicate_provider_event",
                metadata={"provider": event.provider},
            )
            return claim

        normalized_status = normalize_tbank_payment_status(event.provider_status)
        if normalized_status == PaymentStatus.UNKNOWN:
            await self._payment_event_repo.mark_ignored(
                claim.event_id,
                reason="unknown_provider_status",
            )
            await self._audit_log_repo.create(
                action="payment_provider_event_ignored",
                actor_type="provider",
                payment_provider_event_id=claim.event_id,
                reason="unknown_provider_status",
                metadata={"provider": event.provider},
            )
            return claim

        if not event.provider_payment_id:
            await self._fail_unmatched_event(
                claim.event_id,
                event,
                reason="missing_provider_payment_id",
            )
            return claim

        match = await self._payment_transaction_repo.get_with_checkout_by_provider_payment_id(
            provider=event.provider,
            provider_payment_id=event.provider_payment_id,
        )
        if match is None:
            await self._fail_unmatched_event(
                claim.event_id,
                event,
                reason="payment_transaction_not_found",
            )
            return claim

        transaction, checkout, price = match
        mismatch_reason = self._matching_failure_reason(event, transaction, checkout)
        if mismatch_reason is not None:
            await self._fail_unmatched_event(
                claim.event_id,
                event,
                reason=mismatch_reason,
                payment_transaction_id=getattr(transaction, "id", None),
            )
            return claim

        try:
            current_status = PaymentStatus(str(transaction.status))
        except ValueError:
            current_status = PaymentStatus.UNKNOWN
        if _is_stale_payment_status(current_status, normalized_status):
            await self._payment_event_repo.mark_ignored(
                claim.event_id,
                reason="stale_provider_status",
            )
            await self._audit_log_repo.create(
                action="payment_provider_event_stale",
                actor_type="provider",
                payment_transaction_id=transaction.id,
                payment_provider_event_id=claim.event_id,
                old_status=current_status.value,
                new_status=normalized_status.value,
                reason="stale_provider_status",
                metadata={"provider": event.provider},
            )
            return claim

        now = _utcnow()
        paid_at = now if normalized_status == PaymentStatus.SUCCEEDED else None
        refunded_at = now if normalized_status in _REVERSAL_PAYMENT_STATUSES else None
        failure_reason = (
            event.provider_status
            if normalized_status in _FINAL_FAILED_PAYMENT_STATUSES
            else None
        )
        subscription = None
        if normalized_status == PaymentStatus.SUCCEEDED:
            subscription = await self._activate_subscription_once(
                transaction=transaction,
                checkout=checkout,
                price=price,
                at=now,
            )
        subscription_id = (
            getattr(subscription, "id", None)
            or getattr(transaction, "subscription_id", None)
        )

        await self._payment_transaction_repo.update_status(
            transaction_id=transaction.id,
            status=normalized_status.value,
            provider_status=event.provider_status,
            paid_at=paid_at,
            refunded_at=refunded_at,
            failure_reason=failure_reason,
            subscription_id=subscription_id,
        )
        await self._sync_checkout_status(checkout, normalized_status, now)
        await self._payment_event_repo.mark_processed(claim.event_id)
        await self._audit_log_repo.create(
            action="payment_transaction_status_updated",
            actor_type="provider",
            user_id=transaction.user_id,
            subscription_id=subscription_id,
            payment_transaction_id=transaction.id,
            payment_provider_event_id=claim.event_id,
            old_status=current_status.value,
            new_status=normalized_status.value,
            metadata={"provider": event.provider},
        )
        return claim

    async def _activate_subscription_once(
        self,
        transaction,
        checkout,
        price,
        at: datetime,
    ):
        existing_subscription_id = getattr(transaction, "subscription_id", None)
        if existing_subscription_id is not None:
            return None

        current = await self._subscription_repo.lock_current_for_user(transaction.user_id)
        if current is None:
            period_start = at
            period_end = _add_billing_period(period_start, str(price.billing_period))
            subscription = await self._subscription_repo.create_active(
                user_id=transaction.user_id,
                plan_id=checkout.plan_id,
                provider=transaction.provider,
                current_period_start=period_start,
                current_period_end=period_end,
            )
            await self._audit_log_repo.create(
                action="subscription_activated",
                actor_type="provider",
                user_id=transaction.user_id,
                subscription_id=subscription.id,
                payment_transaction_id=transaction.id,
                new_status=SubscriptionStatus.ACTIVE.value,
                reason="payment_confirmed",
                metadata={"billing_period": str(price.billing_period)},
            )
            return subscription

        period_start, period_end = self._renewal_window(current, price, at)
        old_status = str(current.status)
        subscription = await self._subscription_repo.update_active_period(
            subscription_id=current.id,
            plan_id=checkout.plan_id,
            provider=transaction.provider,
            current_period_start=period_start,
            current_period_end=period_end,
        )
        await self._audit_log_repo.create(
            action="subscription_extended",
            actor_type="provider",
            user_id=transaction.user_id,
            subscription_id=current.id,
            payment_transaction_id=transaction.id,
            old_status=old_status,
            new_status=SubscriptionStatus.ACTIVE.value,
            reason="payment_confirmed",
            metadata={"billing_period": str(price.billing_period)},
        )
        return subscription

    @staticmethod
    def _renewal_window(current, price, at: datetime) -> tuple[datetime, datetime]:
        if (
            str(current.status) == SubscriptionStatus.ACTIVE.value
            and current.current_period_end is not None
            and current.current_period_end > at
        ):
            period_start = current.current_period_start or at
            extension_base = current.current_period_end
        else:
            period_start = at
            extension_base = at
        period_end = _add_billing_period(extension_base, str(price.billing_period))
        return period_start, period_end

    async def _fail_unmatched_event(
        self,
        event_id: UUID,
        event: ProviderWebhookEvent,
        *,
        reason: str,
        payment_transaction_id: UUID | None = None,
    ) -> None:
        await self._payment_event_repo.mark_failed(event_id, reason)
        await self._audit_log_repo.create(
            action="payment_provider_event_unmatched",
            actor_type="provider",
            payment_transaction_id=payment_transaction_id,
            payment_provider_event_id=event_id,
            reason=reason,
            metadata={"provider": event.provider},
        )

    @staticmethod
    def _matching_failure_reason(
        event: ProviderWebhookEvent,
        transaction,
        checkout,
    ) -> str | None:
        if transaction.user_id != checkout.user_id:
            return "checkout_user_mismatch"
        if event.provider_order_id is None:
            return "missing_provider_order_id"
        if checkout.provider_order_id != event.provider_order_id:
            return "provider_order_id_mismatch"
        if event.amount_minor is None:
            return "missing_amount"
        if transaction.amount_minor != event.amount_minor:
            return "amount_mismatch"
        if event.currency and transaction.currency.upper() != event.currency.upper():
            return "currency_mismatch"
        return None

    async def _sync_checkout_status(
        self,
        checkout,
        payment_status: PaymentStatus,
        at: datetime,
    ) -> None:
        if payment_status == PaymentStatus.SUCCEEDED:
            await self._checkout_repo.update_status(
                checkout.id,
                status=CheckoutSessionStatus.COMPLETED.value,
                completed_at=at,
            )
            return
        if (
            payment_status in _FINAL_FAILED_PAYMENT_STATUSES
            and checkout.status != CheckoutSessionStatus.COMPLETED.value
        ):
            await self._checkout_repo.update_status(
                checkout.id,
                status=CheckoutSessionStatus.CANCELED.value,
            )


class BillingService:
    """Read-only billing facade for public plans and current user state."""

    def __init__(
        self,
        plan_repo: IBillingPlanRepository,
        subscription_repo: ISubscriptionRepository,
        usage_repo: IUsageEventRepository,
        entitlement_service: EntitlementService,
        checkout_repo: IPaymentCheckoutSessionRepository | None = None,
        payment_transaction_repo: IPaymentTransactionRepository | None = None,
        payment_provider: PaymentProviderClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._plan_repo = plan_repo
        self._subscription_repo = subscription_repo
        self._usage_repo = usage_repo
        self._entitlement_service = entitlement_service
        self._checkout_repo = checkout_repo
        self._payment_transaction_repo = payment_transaction_repo
        self._payment_provider = payment_provider
        self._settings = settings

    async def list_plans(self) -> list[BillingPlanView]:
        """Return active plans without provider-internal identifiers."""
        plans = await self._plan_repo.list_active_plans()
        return [self._to_plan_view(plan) for plan in plans]

    async def get_account_state(self, user_id: str | UUID) -> BillingAccountView:
        """Return current subscription and usage summary for the user."""
        user_uuid = _to_uuid(user_id)
        decision = await self._entitlement_service.check_feature(
            user_uuid,
            AI_OPERATION_FEATURE,
        )
        subscription = await self._subscription_repo.get_current_for_user(user_uuid)
        period_start = decision.period_start or _calendar_month_window(_utcnow())[0]
        period_end = decision.period_end or (period_start + timedelta(days=31))
        usage_summary = await self._usage_repo.summary_for_period(
            user_uuid,
            period_start,
            period_end,
            statuses=["committed"],
        )
        used = usage_summary.get(AI_OPERATION_FEATURE, 0)
        limit_value = decision.limit_value
        remaining = None if limit_value is None else max(limit_value - used, 0)

        return BillingAccountView(
            subscription=self._to_subscription_view(subscription),
            usage=[
                UsageView(
                    feature_code=AI_OPERATION_FEATURE,
                    used=used,
                    limit_value=limit_value,
                    remaining=remaining,
                    period_start=period_start,
                    period_end=period_end,
                )
            ],
        )

    async def create_checkout_session(
        self,
        user_id: str | UUID,
        plan_code: str,
        idempotency_key: str | None = None,
    ) -> CheckoutSessionResult:
        """Create a non-activating provider checkout reference.

        The caller provides only a plan code. Price, currency, provider and URLs
        are derived server-side. This method is intentionally not exposed as a
        public route until a real provider integration is ready.
        """
        if self._checkout_repo is None or self._payment_provider is None:
            raise PaymentProviderDisabledError("Checkout provider is not configured")
        if self._settings is None:
            raise PaymentProviderDisabledError("Checkout URLs are not configured")

        plan = await self._plan_repo.get_plan_by_code(plan_code)
        if plan is None or not plan.is_active:
            raise ValueError("Unknown or inactive billing plan")

        price = await self._plan_repo.get_active_price(
            plan_code=plan_code,
            provider=self._payment_provider.provider_name,
        )
        if price is None:
            raise PaymentProviderDisabledError("No active provider price is configured")
        if self._payment_transaction_repo is None:
            raise PaymentProviderDisabledError(
                "Payment transaction repository is not configured"
            )

        user_uuid = _to_uuid(user_id)
        reusable = await self._checkout_repo.find_reusable(
            user_id=user_uuid,
            plan_id=plan.id,
            price_id=price.id,
            provider=self._payment_provider.provider_name,
            at=_utcnow(),
        )
        if reusable is not None:
            return CheckoutSessionResult(
                provider=reusable.provider,
                provider_session_id=reusable.provider_session_id,
                payment_url=reusable.payment_url,
                provider_order_id=reusable.provider_order_id,
                status=reusable.status,
                expires_at=reusable.expires_at,
                can_activate_entitlement=False,
            )

        frontend_url = self._settings.frontend_url.rstrip("/")
        request = CheckoutSessionRequest(
            user_id=user_uuid,
            plan_code=plan_code,
            amount_minor=price.amount_minor,
            currency=price.currency,
            provider_price_id=price.provider_price_id,
            success_url=f"{frontend_url}/billing/success",
            cancel_url=f"{frontend_url}/billing/cancel",
            idempotency_key=idempotency_key,
        )
        result = await self._payment_provider.create_checkout_session(request)
        if result.can_activate_entitlement:
            raise PaymentProviderDisabledError(
                "Checkout session cannot activate entitlements directly"
            )
        checkout = await self._checkout_repo.create(
            user_id=request.user_id,
            plan_id=plan.id,
            price_id=price.id,
            provider=result.provider,
            provider_session_id=result.provider_session_id,
            provider_order_id=result.provider_order_id,
            payment_url=result.payment_url,
            idempotency_key=idempotency_key,
            status=result.status,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            expires_at=result.expires_at,
        )
        initial_status = normalize_tbank_payment_status(result.provider_status)
        if initial_status == PaymentStatus.UNKNOWN:
            initial_status = PaymentStatus.PENDING
        await self._payment_transaction_repo.create(
            user_id=request.user_id,
            checkout_session_id=checkout.id,
            provider=result.provider,
            provider_payment_id=result.provider_session_id,
            amount_minor=price.amount_minor,
            currency=price.currency,
            status=initial_status.value,
            provider_status=result.provider_status,
        )
        return result

    @staticmethod
    def _to_plan_view(plan) -> BillingPlanView:
        prices = [
            BillingPriceView(
                provider=price.provider,
                amount_minor=price.amount_minor,
                currency=price.currency,
                billing_period=price.billing_period,
            )
            for price in getattr(plan, "prices", [])
            if price.is_active
        ]
        entitlements = [
            PlanEntitlementView(
                feature_code=entitlement.feature_code,
                limit_value=entitlement.limit_value,
                reset_period=entitlement.reset_period,
            )
            for entitlement in getattr(plan, "entitlements", [])
        ]
        return BillingPlanView(
            code=plan.code,
            title=plan.title,
            description=plan.description,
            billing_period=plan.billing_period,
            trial_days=plan.trial_days,
            prices=prices,
            entitlements=entitlements,
        )

    @staticmethod
    def _to_subscription_view(subscription) -> SubscriptionView | None:
        if subscription is None:
            return None
        plan = getattr(subscription, "plan", None)
        return SubscriptionView(
            status=subscription.status,
            plan_code=getattr(plan, "code", None),
            trial_end=subscription.trial_end,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
