"""Payment provider contracts.

Provider implementations must never expose raw card data to the application.
They should return only provider references, hosted checkout URLs and sanitized
status fields.
"""

from __future__ import annotations

from typing import Protocol

from backend.domain.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResult,
    ProviderWebhookEvent,
)


class PaymentProviderDisabledError(RuntimeError):
    """Raised when live payment provider functionality is intentionally disabled."""


class PaymentProviderClient(Protocol):
    """Protocol for hosted checkout and signed webhook providers."""

    provider_name: str

    async def create_checkout_session(
        self,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResult:
        """Create a hosted checkout session from server-controlled data."""

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Verify and sanitize a provider webhook event."""
