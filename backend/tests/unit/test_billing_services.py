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

    async def get_current_for_user(self, user_id):
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
            provider_price_id="noop_basic_monthly",
        )

    async def list_active_plans(self):
        return [self.plan]

    async def get_plan_by_code(self, code):
        return self.plan if code == self.plan.code else None

    async def get_active_price(self, plan_code, provider):
        if plan_code == self.plan.code and provider == "noop":
            return self.price
        return None


class FakeCheckoutRepo:
    def __init__(self) -> None:
        self.created = []

    async def create(self, **kwargs):
        self.created.append(kwargs)
        return SimpleNamespace(id=uuid4(), **kwargs)


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
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(event_repo, audit_repo)
    event = ProviderWebhookEvent(
        provider="tbank",
        provider_event_id="evt_1",
        event_type="payment",
        payload_hash="a" * 64,
        provider_payment_id="pay_1",
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
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(event_repo, audit_repo)
    original = ProviderWebhookEvent(
        provider="tbank",
        provider_event_id="evt_mismatch",
        event_type="payment",
        payload_hash="a" * 64,
        provider_payment_id="pay_1",
        provider_status="CONFIRMED",
    )
    tampered = ProviderWebhookEvent(
        provider="tbank",
        provider_event_id="evt_mismatch",
        event_type="payment",
        payload_hash="b" * 64,
        provider_payment_id="pay_1",
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
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(event_repo, audit_repo)

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
    audit_repo = FakeAuditRepo()
    service = PaymentWebhookService(event_repo, audit_repo)

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
async def test_noop_checkout_is_server_priced_and_non_activating(settings):
    plan_repo = FakePlanRepo()
    checkout_repo = FakeCheckoutRepo()
    billing = BillingService(
        plan_repo=plan_repo,
        subscription_repo=FakeSubscriptionRepo(),
        usage_repo=FakeUsageRepo(),
        entitlement_service=EntitlementService(FakeSubscriptionRepo(), settings),
        checkout_repo=checkout_repo,
        payment_provider=NoopPaymentProvider(),
        settings=SimpleNamespace(frontend_url="https://example.com"),
    )

    result = await billing.create_checkout_session(uuid4(), "basic")

    assert result.can_activate_entitlement is False
    assert result.payment_url is None
    assert result.status == CheckoutSessionStatus.CREATED.value
    assert checkout_repo.created[0]["success_url"] == "https://example.com/billing/success"
    assert checkout_repo.created[0]["cancel_url"] == "https://example.com/billing/cancel"


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
