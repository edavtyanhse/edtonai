"""Unit tests for billing entitlement and usage services."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.config import Settings
from backend.domain.billing import (
    AI_OPERATION_FEATURE,
    CheckoutSessionResult,
    CheckoutSessionStatus,
    PaymentStatus,
    ProviderEventClaim,
    ProviderWebhookEvent,
)
from backend.errors.business import EntitlementDeniedError
from backend.integration.payments.base import PaymentProviderDisabledError
from backend.integration.payments.noop import NoopPaymentProvider
from backend.services.billing import (
    BillingService,
    EntitlementService,
    PaymentStatusMapper,
    PaymentWebhookService,
    SubscriptionStateMachine,
    UsageService,
)


class FakeSubscriptionRepo:
    def __init__(self, subscription=None) -> None:
        self.subscription = subscription
        self.lock_calls = 0
        self.created = []
        self.updated = []

    async def get_current_for_user(self, user_id):
        return self.subscription

    async def lock_current_for_user(self, user_id):
        self.lock_calls += 1
        return self.subscription

    async def create_active(
        self,
        user_id,
        plan_id,
        provider,
        current_period_start,
        current_period_end,
    ):
        subscription = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            plan_id=plan_id,
            provider=provider,
            status="active",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
        )
        self.subscription = subscription
        self.created.append(subscription)
        return subscription

    async def update_active_period(
        self,
        subscription_id,
        plan_id,
        provider,
        current_period_start,
        current_period_end,
    ):
        if self.subscription is None:
            return None
        self.subscription.plan_id = plan_id
        self.subscription.provider = provider
        self.subscription.status = "active"
        self.subscription.current_period_start = current_period_start
        self.subscription.current_period_end = current_period_end
        self.updated.append(
            (
                subscription_id,
                plan_id,
                provider,
                current_period_start,
                current_period_end,
            )
        )
        return self.subscription


class FakeUsageRepo:
    def __init__(self, used: int = 0) -> None:
        self.used = used
        self.events = {}
        self.lock_calls = 0

    async def acquire_period_lock(self, user_id, feature_code, period_start) -> None:
        self.lock_calls += 1

    async def get_by_idempotency_key(self, user_id, feature_code, idempotency_key):
        return self.events.get(idempotency_key)

    async def count_for_period(
        self,
        user_id,
        feature_code,
        period_start,
        period_end,
        statuses,
    ) -> int:
        return self.used

    async def summary_for_period(self, user_id, period_start, period_end, statuses):
        return {AI_OPERATION_FEATURE: self.used}

    async def create(
        self,
        user_id,
        feature_code,
        operation,
        quantity,
        status,
        idempotency_key=None,
        subscription_id=None,
        period_start=None,
        period_end=None,
        resource_type=None,
        resource_id=None,
        metadata=None,
    ):
        event = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            feature_code=feature_code,
            operation=operation,
            quantity=quantity,
            status=status,
            idempotency_key=idempotency_key,
        )
        self.events[idempotency_key] = event
        return event

    async def update_status(self, event_id, status):
        for event in self.events.values():
            if event.id == event_id:
                event.status = status
                return event
        return None


class FakePaymentEventRepo:
    def __init__(self) -> None:
        self.events = {}
        self.processed = []
        self.ignored = []
        self.failed = []
        self.payloads = {}

    async def claim_provider_event(
        self,
        provider,
        provider_event_id,
        event_type,
        payload_hash,
        provider_payment_id=None,
        provider_subscription_id=None,
        provider_status=None,
    ):
        key = (provider, provider_event_id)
        if key in self.events:
            return ProviderEventClaim(
                event_id=self.events[key],
                is_duplicate=True,
                processing_status="processed",
            )
        event_id = uuid4()
        self.events[key] = event_id
        self.payloads[event_id] = {
            "payload_hash": payload_hash,
            "provider_payment_id": provider_payment_id,
            "provider_subscription_id": provider_subscription_id,
            "provider_status": provider_status,
        }
        return ProviderEventClaim(
            event_id=event_id,
            is_duplicate=False,
            processing_status="received",
        )

    async def payload_matches(
        self,
        event_id,
        payload_hash,
        provider_payment_id=None,
        provider_subscription_id=None,
        provider_status=None,
    ):
        return self.payloads.get(event_id) == {
            "payload_hash": payload_hash,
            "provider_payment_id": provider_payment_id,
            "provider_subscription_id": provider_subscription_id,
            "provider_status": provider_status,
        }

    async def mark_processed(self, event_id):
        self.processed.append(event_id)

    async def mark_ignored(self, event_id, reason=None):
        self.ignored.append((event_id, reason))

    async def mark_failed(self, event_id, error):
        self.failed.append((event_id, error))


class FakeAuditRepo:
    def __init__(self) -> None:
        self.events = []

    async def create(self, **kwargs):
        self.events.append(kwargs)
        return SimpleNamespace(id=uuid4(), **kwargs)


class FakePlanRepo:
    def __init__(self) -> None:
        self.plan = SimpleNamespace(id=uuid4(), code="basic", is_active=True)
        self.price = SimpleNamespace(
            id=uuid4(),
            amount_minor=49000,
            currency="RUB",
            billing_period="month",
            provider_price_id="noop_basic_monthly",
        )

    async def list_active_plans(self):
        return [self.plan]

    async def get_plan_by_code(self, code):
        return self.plan if code == self.plan.code else None

    async def get_active_price(self, plan_code, provider):
        if plan_code == self.plan.code and provider in {"noop", "fake"}:
            return self.price
        return None


class FakeCheckoutRepo:
    def __init__(self) -> None:
        self.created = []
        self.reusable = None
        self.status_updates = []

    async def create(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(id=uuid4(), **kwargs)

    async def find_reusable(self, **kwargs):
        return self.reusable

    async def update_status(self, checkout_session_id, status, completed_at=None):
        self.status_updates.append((checkout_session_id, status, completed_at))
        return SimpleNamespace(
            id=checkout_session_id,
            status=status,
            completed_at=completed_at,
        )


class FakePaymentTransactionRepo:
    def __init__(self) -> None:
        self.created = []
        self.matches = {}
        self.transactions_by_id = {}
        self.status_updates = []

    async def create(self, **kwargs):
        transaction = SimpleNamespace(id=uuid4(), **kwargs)
        self.created.append(transaction)
        self.transactions_by_id[transaction.id] = transaction
        return transaction

    def add_match(self, transaction, checkout, price):
        self.matches[(transaction.provider, transaction.provider_payment_id)] = (
            transaction,
            checkout,
            price,
        )
        self.transactions_by_id[transaction.id] = transaction

    async def get_with_checkout_by_provider_payment_id(
        self,
        provider,
        provider_payment_id,
    ):
        return self.matches.get((provider, provider_payment_id))

    async def update_status(
        self,
        transaction_id,
        status,
        provider_status=None,
        paid_at=None,
        refunded_at=None,
        failure_reason=None,
        subscription_id=None,
    ):
        transaction = self.transactions_by_id[transaction_id]
        transaction.status = status
        transaction.provider_status = provider_status
        if subscription_id is not None:
            transaction.subscription_id = subscription_id
        if paid_at is not None:
            transaction.paid_at = paid_at
        if refunded_at is not None:
            transaction.refunded_at = refunded_at
        transaction.failure_reason = failure_reason
        self.status_updates.append(
            (transaction_id, status, provider_status, paid_at, refunded_at)
        )
        return transaction


def _matched_payment(
    *,
    status: str = PaymentStatus.PENDING.value,
    payment_id: str = "pay_1",
    order_id: str = "order_1",
    amount_minor: int = 49000,
    billing_period: str = "month",
    subscription_id=None,
):
    user_id = uuid4()
    plan_id = uuid4()
    transaction = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        subscription_id=subscription_id,
        provider="tbank",
        provider_payment_id=payment_id,
        amount_minor=amount_minor,
        currency="RUB",
        status=status,
        provider_status="NEW",
    )
    checkout = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        plan_id=plan_id,
        provider="tbank",
        provider_order_id=order_id,
        status=CheckoutSessionStatus.CREATED.value,
    )
    price = SimpleNamespace(
        id=uuid4(),
        plan_id=plan_id,
        billing_period=billing_period,
        amount_minor=amount_minor,
        currency="RUB",
    )
    transaction_repo = FakePaymentTransactionRepo()
    transaction_repo.add_match(transaction, checkout, price)
    return transaction_repo, transaction, checkout, price


class FakeLivePaymentProvider:
    provider_name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    async def create_checkout_session(self, request):
        self.calls += 1
        return CheckoutSessionResult(
            provider=self.provider_name,
            provider_session_id=f"fake_session_{self.calls}",
            payment_url=f"https://pay.example.com/{self.calls}",
            provider_order_id=f"order_{self.calls}",
            status=CheckoutSessionStatus.CREATED.value,
            can_activate_entitlement=False,
        )

    async def verify_webhook(self, payload, headers):
        raise NotImplementedError


@pytest.fixture
def settings():
    return SimpleNamespace(ai_monthly_free_quota=2, ai_monthly_trial_quota=5)


def _plan(entitlements):
    return SimpleNamespace(
        code="pro",
        entitlements=[
            SimpleNamespace(
                feature_code=feature_code,
                limit_value=limit_value,
                reset_period="month",
            )
            for feature_code, limit_value in entitlements
        ],
    )


def _subscription(status: str, *, plan=None, days: int = 10):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        status=status,
        plan=plan or _plan([(AI_OPERATION_FEATURE, 100)]),
        trial_start=now - timedelta(days=1),
        trial_end=now + timedelta(days=days),
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=days),
        cancel_at_period_end=False,
    )


@pytest.mark.anyio
async def test_free_user_gets_settings_backed_quota(settings):
    service = EntitlementService(FakeSubscriptionRepo(), settings)

    decision = await service.check_feature(uuid4(), AI_OPERATION_FEATURE)

    assert decision.allowed is True
    assert decision.plan_code == "free"
    assert decision.limit_value == 2


@pytest.mark.anyio
async def test_expired_trial_denies_fail_closed(settings):
    subscription = _subscription("trialing", days=-1)
    service = EntitlementService(FakeSubscriptionRepo(subscription), settings)

    decision = await service.check_feature(uuid4(), AI_OPERATION_FEATURE)

    assert decision.allowed is False
    assert decision.reason == "trial_expired"


@pytest.mark.anyio
async def test_past_due_denies_even_when_subscription_is_current(settings):
    subscription = _subscription("past_due")
    service = EntitlementService(FakeSubscriptionRepo(subscription), settings)

    decision = await service.check_feature(uuid4(), AI_OPERATION_FEATURE)

    assert decision.allowed is False
    assert decision.reason == "subscription_past_due"


@pytest.mark.anyio
async def test_terminal_subscription_statuses_deny_entitlements(settings):
    for status in ("canceled", "expired"):
        subscription = _subscription(status)
        service = EntitlementService(FakeSubscriptionRepo(subscription), settings)

        decision = await service.check_feature(uuid4(), AI_OPERATION_FEATURE)

        assert decision.allowed is False
        assert decision.reason == f"subscription_{status}"


@pytest.mark.anyio
async def test_active_plan_reads_limit_from_plan_entitlement(settings):
    subscription = _subscription("active", plan=_plan([(AI_OPERATION_FEATURE, 17)]))
    service = EntitlementService(FakeSubscriptionRepo(subscription), settings)

    decision = await service.check_feature(uuid4(), AI_OPERATION_FEATURE)

    assert decision.allowed is True
    assert decision.limit_value == 17
    assert decision.plan_code == "pro"


@pytest.mark.anyio
async def test_active_plan_requires_matching_entitlement(settings):
    subscription = _subscription("active", plan=_plan([]))
    service = EntitlementService(FakeSubscriptionRepo(subscription), settings)

    decision = await service.check_feature(uuid4(), AI_OPERATION_FEATURE)

    assert decision.allowed is False
    assert decision.reason == "feature_not_in_plan"


@pytest.mark.anyio
async def test_usage_reserve_commit_and_cancel(settings):
    entitlement = EntitlementService(FakeSubscriptionRepo(), settings)
    usage_repo = FakeUsageRepo(used=0)
    usage = UsageService(entitlement, usage_repo)

    reservation = await usage.reserve(
        user_id=uuid4(),
        feature_code=AI_OPERATION_FEATURE,
        operation="parse_resume",
        idempotency_key="parse_resume:test",
    )
    await usage.commit(reservation)

    assert usage_repo.lock_calls == 1
    assert usage_repo.events["parse_resume:test"].status == "committed"


@pytest.mark.anyio
async def test_duplicate_committed_usage_does_not_allow_provider_call(settings):
    entitlement = EntitlementService(FakeSubscriptionRepo(), settings)
    usage_repo = FakeUsageRepo(used=0)
    usage = UsageService(entitlement, usage_repo)

    first = await usage.reserve(
        user_id=uuid4(),
        feature_code=AI_OPERATION_FEATURE,
        operation="parse_resume",
        idempotency_key="parse_resume:same-hash",
    )
    await usage.commit(first)
    second = await usage.reserve(
        user_id=first.user_id,
        feature_code=AI_OPERATION_FEATURE,
        operation="parse_resume",
        idempotency_key="parse_resume:same-hash",
    )

    assert second.status == "committed"
    assert second.provider_call_allowed is False


@pytest.mark.anyio
async def test_usage_denies_when_quota_exhausted(settings):
    entitlement = EntitlementService(FakeSubscriptionRepo(), settings)
    usage = UsageService(entitlement, FakeUsageRepo(used=2))

    with pytest.raises(EntitlementDeniedError, match="Monthly quota exceeded"):
        await usage.reserve(
            user_id=uuid4(),
            feature_code=AI_OPERATION_FEATURE,
            operation="parse_resume",
            idempotency_key="parse_resume:test",
        )


@pytest.mark.anyio
async def test_track_ai_call_cancels_reservation_on_error(settings):
    entitlement = EntitlementService(FakeSubscriptionRepo(), settings)
    usage_repo = FakeUsageRepo(used=0)
    usage = UsageService(entitlement, usage_repo)

    with pytest.raises(RuntimeError):
        async with usage.track_ai_call(uuid4(), "parse_resume", "hash"):
            raise RuntimeError("provider failed")

    event = usage_repo.events["parse_resume:hash"]
    assert event.status == "failed"


def test_tbank_status_mapping_preserves_provider_specific_detail():
    assert PaymentStatusMapper.from_tbank("AUTHORIZED") == PaymentStatus.AUTHORIZED
    assert PaymentStatusMapper.from_tbank("CONFIRMED") == PaymentStatus.SUCCEEDED
    assert PaymentStatusMapper.from_tbank("PARTIAL_REFUNDED") == (
        PaymentStatus.PARTIALLY_REFUNDED
    )
    assert PaymentStatusMapper.from_tbank("unexpected") == PaymentStatus.UNKNOWN


def test_subscription_state_machine_rejects_terminal_reactivation():
    assert SubscriptionStateMachine.can_transition("trialing", "active") is True
    assert SubscriptionStateMachine.can_transition("canceled", "active") is False


@pytest.mark.anyio
async def test_webhook_service_claims_duplicate_events_without_reprocessing():
    event_repo = FakePaymentEventRepo()
    transaction_repo, _, _, _ = _matched_payment()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )
    event = ProviderWebhookEvent(
        provider="tbank",
        provider_event_id="evt_1",
        event_type="payment",
        payload_hash="a" * 64,
        provider_payment_id="pay_1",
        provider_order_id="order_1",
        amount_minor=49000,
        provider_status="CONFIRMED",
    )

    first = await service.process_verified_event(event, signature_verified=True)
    second = await service.process_verified_event(event, signature_verified=True)

    assert first.is_duplicate is False
    assert second.is_duplicate is True
    assert len(event_repo.processed) == 1
    assert audit_repo.events[-1]["action"] == "payment_provider_event_duplicate"


@pytest.mark.anyio
async def test_webhook_service_flags_duplicate_payload_mismatch():
    event_repo = FakePaymentEventRepo()
    transaction_repo, _, _, _ = _matched_payment()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )
    original = ProviderWebhookEvent(
        provider="tbank",
        provider_event_id="evt_mismatch",
        event_type="payment",
        payload_hash="a" * 64,
        provider_payment_id="pay_1",
        provider_order_id="order_1",
        amount_minor=49000,
        provider_status="CONFIRMED",
    )
    tampered = ProviderWebhookEvent(
        provider="tbank",
        provider_event_id="evt_mismatch",
        event_type="payment",
        payload_hash="b" * 64,
        provider_payment_id="pay_1",
        provider_order_id="order_1",
        amount_minor=49000,
        provider_status="REFUNDED",
    )

    await service.process_verified_event(original, signature_verified=True)
    second = await service.process_verified_event(tampered, signature_verified=True)

    assert second.is_duplicate is True
    assert event_repo.failed == [
        (second.event_id, "duplicate_provider_event_payload_mismatch")
    ]
    assert audit_repo.events[-1]["action"] == "payment_provider_event_payload_mismatch"


@pytest.mark.anyio
async def test_webhook_service_rejects_unverified_event_before_mutation():
    event_repo = FakePaymentEventRepo()
    transaction_repo = FakePaymentTransactionRepo()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    with pytest.raises(PaymentProviderDisabledError):
        await service.process_verified_event(
            ProviderWebhookEvent(
                provider="tbank",
                provider_event_id="evt_unsigned",
                event_type="payment",
                payload_hash="c" * 64,
                provider_status="CONFIRMED",
            ),
            signature_verified=False,
        )

    assert event_repo.events == {}
    assert audit_repo.events == []


@pytest.mark.anyio
async def test_webhook_service_ignores_unknown_provider_status_fail_closed():
    event_repo = FakePaymentEventRepo()
    transaction_repo = FakePaymentTransactionRepo()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    claim = await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_unknown",
            event_type="payment",
            payload_hash="b" * 64,
            provider_status="MYSTERY",
        ),
        signature_verified=True,
    )

    assert claim.is_duplicate is False
    assert event_repo.ignored == [(claim.event_id, "unknown_provider_status")]
    assert audit_repo.events[-1]["action"] == "payment_provider_event_ignored"


@pytest.mark.anyio
async def test_webhook_service_fails_unknown_payment_id():
    event_repo = FakePaymentEventRepo()
    transaction_repo = FakePaymentTransactionRepo()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    claim = await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_unknown_payment",
            event_type="payment",
            payload_hash="d" * 64,
            provider_payment_id="missing",
            provider_order_id="order_1",
            amount_minor=49000,
            provider_status="CONFIRMED",
        ),
        signature_verified=True,
    )

    assert event_repo.failed == [(claim.event_id, "payment_transaction_not_found")]
    assert audit_repo.events[-1]["action"] == "payment_provider_event_unmatched"


@pytest.mark.anyio
async def test_webhook_service_fails_order_id_mismatch():
    event_repo = FakePaymentEventRepo()
    transaction_repo, _, _, _ = _matched_payment()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    claim = await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_order_mismatch",
            event_type="payment",
            payload_hash="e" * 64,
            provider_payment_id="pay_1",
            provider_order_id="other_order",
            amount_minor=49000,
            provider_status="CONFIRMED",
        ),
        signature_verified=True,
    )

    assert event_repo.failed == [(claim.event_id, "provider_order_id_mismatch")]
    assert transaction_repo.status_updates == []
    assert checkout_repo.status_updates == []


@pytest.mark.anyio
async def test_webhook_service_fails_amount_mismatch():
    event_repo = FakePaymentEventRepo()
    transaction_repo, _, _, _ = _matched_payment()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    claim = await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_amount_mismatch",
            event_type="payment",
            payload_hash="f" * 64,
            provider_payment_id="pay_1",
            provider_order_id="order_1",
            amount_minor=1,
            provider_status="CONFIRMED",
        ),
        signature_verified=True,
    )

    assert event_repo.failed == [(claim.event_id, "amount_mismatch")]
    assert transaction_repo.status_updates == []
    assert checkout_repo.status_updates == []


@pytest.mark.anyio
async def test_webhook_service_updates_matched_transaction_and_checkout():
    event_repo = FakePaymentEventRepo()
    transaction_repo, transaction, checkout, _ = _matched_payment()
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    claim = await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_confirmed",
            event_type="payment",
            payload_hash="1" * 64,
            provider_payment_id="pay_1",
            provider_order_id="order_1",
            amount_minor=49000,
            provider_status="CONFIRMED",
        ),
        signature_verified=True,
    )

    assert event_repo.processed == [claim.event_id]
    assert transaction.status == PaymentStatus.SUCCEEDED.value
    assert transaction.paid_at is not None
    assert transaction.subscription_id == subscription_repo.created[0].id
    assert subscription_repo.created[0].status == "active"
    assert checkout_repo.status_updates[0][0] == checkout.id
    assert checkout_repo.status_updates[0][1] == CheckoutSessionStatus.COMPLETED.value
    assert audit_repo.events[-1]["action"] == "payment_transaction_status_updated"


@pytest.mark.anyio
async def test_webhook_service_extends_existing_active_subscription():
    event_repo = FakePaymentEventRepo()
    transaction_repo, transaction, _, _ = _matched_payment(billing_period="week")
    checkout_repo = FakeCheckoutRepo()
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=5)
    current_end = now + timedelta(days=2)
    subscription = SimpleNamespace(
        id=uuid4(),
        user_id=transaction.user_id,
        plan_id=uuid4(),
        provider="tbank",
        status="active",
        current_period_start=current_start,
        current_period_end=current_end,
    )
    subscription_repo = FakeSubscriptionRepo(subscription)
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_extend",
            event_type="payment",
            payload_hash="3" * 64,
            provider_payment_id="pay_1",
            provider_order_id="order_1",
            amount_minor=49000,
            provider_status="CONFIRMED",
        ),
        signature_verified=True,
    )

    assert subscription_repo.created == []
    assert subscription_repo.updated[0][0] == subscription.id
    assert subscription.current_period_start == current_start
    assert subscription.current_period_end == current_end + timedelta(days=7)
    assert transaction.subscription_id == subscription.id
    assert any(event["action"] == "subscription_extended" for event in audit_repo.events)


@pytest.mark.anyio
async def test_webhook_service_does_not_extend_transaction_already_linked_to_subscription():
    existing_subscription_id = uuid4()
    event_repo = FakePaymentEventRepo()
    transaction_repo, transaction, _, _ = _matched_payment(
        subscription_id=existing_subscription_id,
    )
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_already_linked",
            event_type="payment",
            payload_hash="4" * 64,
            provider_payment_id="pay_1",
            provider_order_id="order_1",
            amount_minor=49000,
            provider_status="CONFIRMED",
        ),
        signature_verified=True,
    )

    assert transaction.subscription_id == existing_subscription_id
    assert subscription_repo.lock_calls == 0
    assert subscription_repo.created == []
    assert subscription_repo.updated == []


@pytest.mark.anyio
async def test_webhook_service_ignores_out_of_order_status_after_success():
    event_repo = FakePaymentEventRepo()
    transaction_repo, transaction, _, _ = _matched_payment(
        status=PaymentStatus.SUCCEEDED.value,
    )
    checkout_repo = FakeCheckoutRepo()
    subscription_repo = FakeSubscriptionRepo()
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(
        event_repo,
        transaction_repo,
        checkout_repo,
        subscription_repo,
        audit_repo,
    )

    claim = await service.process_verified_event(
        ProviderWebhookEvent(
            provider="tbank",
            provider_event_id="evt_stale_authorized",
            event_type="payment",
            payload_hash="2" * 64,
            provider_payment_id="pay_1",
            provider_order_id="order_1",
            amount_minor=49000,
            provider_status="AUTHORIZED",
        ),
        signature_verified=True,
    )

    assert event_repo.ignored == [(claim.event_id, "stale_provider_status")]
    assert transaction.status == PaymentStatus.SUCCEEDED.value
    assert transaction_repo.status_updates == []
    assert checkout_repo.status_updates == []


@pytest.mark.anyio
async def test_noop_checkout_fails_closed_without_creating_session(settings):
    plan_repo = FakePlanRepo()
    checkout_repo = FakeCheckoutRepo()
    billing = BillingService(
        plan_repo=plan_repo,
        subscription_repo=FakeSubscriptionRepo(),
        usage_repo=FakeUsageRepo(),
        entitlement_service=EntitlementService(FakeSubscriptionRepo(), settings),
        checkout_repo=checkout_repo,
        payment_transaction_repo=FakePaymentTransactionRepo(),
        payment_provider=NoopPaymentProvider(),
        settings=SimpleNamespace(frontend_url="https://example.com"),
    )

    with pytest.raises(PaymentProviderDisabledError):
        await billing.create_checkout_session(uuid4(), "basic")

    assert checkout_repo.created == []


@pytest.mark.anyio
async def test_checkout_unknown_plan_raises_before_provider_call(settings):
    checkout_repo = FakeCheckoutRepo()
    billing = BillingService(
        plan_repo=FakePlanRepo(),
        subscription_repo=FakeSubscriptionRepo(),
        usage_repo=FakeUsageRepo(),
        entitlement_service=EntitlementService(FakeSubscriptionRepo(), settings),
        checkout_repo=checkout_repo,
        payment_transaction_repo=FakePaymentTransactionRepo(),
        payment_provider=NoopPaymentProvider(),
        settings=SimpleNamespace(frontend_url="https://example.com"),
    )

    with pytest.raises(ValueError, match="Unknown or inactive billing plan"):
        await billing.create_checkout_session(uuid4(), "missing")

    assert checkout_repo.created == []


@pytest.mark.anyio
async def test_checkout_persists_provider_order_url_and_idempotency(settings):
    checkout_repo = FakeCheckoutRepo()
    transaction_repo = FakePaymentTransactionRepo()
    provider = FakeLivePaymentProvider()
    billing = BillingService(
        plan_repo=FakePlanRepo(),
        subscription_repo=FakeSubscriptionRepo(),
        usage_repo=FakeUsageRepo(),
        entitlement_service=EntitlementService(FakeSubscriptionRepo(), settings),
        checkout_repo=checkout_repo,
        payment_transaction_repo=transaction_repo,
        payment_provider=provider,
        settings=SimpleNamespace(frontend_url="https://example.com"),
    )

    result = await billing.create_checkout_session(
        uuid4(),
        "basic",
        idempotency_key="checkout-key-1",
    )

    assert result.provider_order_id == "order_1"
    assert checkout_repo.created[0]["provider_order_id"] == "order_1"
    assert checkout_repo.created[0]["payment_url"] == "https://pay.example.com/1"
    assert checkout_repo.created[0]["idempotency_key"] == "checkout-key-1"
    assert transaction_repo.created[0].provider_payment_id == "fake_session_1"
    assert transaction_repo.created[0].amount_minor == 49000
    assert transaction_repo.created[0].currency == "RUB"
    assert transaction_repo.created[0].status == PaymentStatus.PENDING.value


@pytest.mark.anyio
async def test_checkout_reuses_active_session_without_provider_call(settings):
    checkout_repo = FakeCheckoutRepo()
    checkout_repo.reusable = SimpleNamespace(
        provider="fake",
        provider_session_id="existing_session",
        provider_order_id="existing_order",
        payment_url="https://pay.example.com/existing",
        status=CheckoutSessionStatus.CREATED.value,
        expires_at=None,
    )
    provider = FakeLivePaymentProvider()
    billing = BillingService(
        plan_repo=FakePlanRepo(),
        subscription_repo=FakeSubscriptionRepo(),
        usage_repo=FakeUsageRepo(),
        entitlement_service=EntitlementService(FakeSubscriptionRepo(), settings),
        checkout_repo=checkout_repo,
        payment_transaction_repo=FakePaymentTransactionRepo(),
        payment_provider=provider,
        settings=SimpleNamespace(frontend_url="https://example.com"),
    )

    result = await billing.create_checkout_session(uuid4(), "basic")

    assert result.provider_session_id == "existing_session"
    assert result.provider_order_id == "existing_order"
    assert result.payment_url == "https://pay.example.com/existing"
    assert provider.calls == 0
    assert checkout_repo.created == []


def test_production_requires_explicit_flag_for_temporary_huge_free_quota():
    kwargs = {
        "postgres_user": "u",
        "postgres_password": "p",
        "postgres_host": "localhost",
        "postgres_port": 5432,
        "postgres_db": "db",
        "log_level": "INFO",
        "app_env": "production",
        "jwt_secret_key": "x" * 32,
        "ai_monthly_free_quota": 1_000_000,
        "billing_temporary_high_free_quota_enabled": False,
    }

    with pytest.raises(ValidationError):
        Settings(**kwargs)

    settings = Settings(
        **{
            **kwargs,
            "billing_temporary_high_free_quota_enabled": True,
        }
    )
    assert settings.ai_monthly_free_quota == 1_000_000


def test_example_like_production_config_does_not_enable_huge_quota_by_default():
    with pytest.raises(ValidationError):
        Settings(
            postgres_user="u",
            postgres_password="p",
            postgres_host="localhost",
            postgres_port=5432,
            postgres_db="db",
            log_level="INFO",
            app_env="production",
            jwt_secret_key="x" * 32,
            ai_monthly_free_quota=1_000_000,
            billing_temporary_high_free_quota_enabled=False,
        )
