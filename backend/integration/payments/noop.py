"""Non-activating payment provider for pre-integration wiring."""

from __future__ import annotations

from backend.domain.billing import (
    CheckoutSessionRequest,
    ProviderWebhookEvent,
)
from backend.integration.payments.base import PaymentProviderDisabledError


class NoopPaymentProvider:
    """Fail-closed provider used before a real payment provider is connected."""

    provider_name = "noop"

    async def create_checkout_session(
        self,
        request: CheckoutSessionRequest,
    ):
        """Reject public checkout creation while payments are disabled."""
        raise PaymentProviderDisabledError(
            "Payment provider is disabled and cannot create checkout sessions"
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
