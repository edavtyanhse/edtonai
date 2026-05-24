"""Non-activating payment provider for pre-integration wiring."""

from __future__ import annotations

from uuid import uuid4

from backend.domain.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResult,
    CheckoutSessionStatus,
    ProviderWebhookEvent,
)
from backend.integration.payments.base import PaymentProviderDisabledError


class NoopPaymentProvider:
    """Fail-closed provider used before a real payment provider is connected."""

    provider_name = "noop"

    async def create_checkout_session(
        self,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResult:
        """Return a non-activating checkout reference without a payment URL."""
        return CheckoutSessionResult(
            provider=self.provider_name,
            provider_session_id=f"noop_{uuid4()}",
            payment_url=None,
            status=CheckoutSessionStatus.CREATED.value,
            expires_at=None,
            provider_status="disabled",
            can_activate_entitlement=False,
        )

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Noop webhooks are not trusted and must not activate access."""
        raise PaymentProviderDisabledError(
            "Noop payment provider does not verify live webhook events"
        )
