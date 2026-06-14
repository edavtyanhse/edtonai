"""T-Bank internet acquiring hosted checkout adapter."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlparse
from uuid import uuid4

import httpx
from pydantic import SecretStr

from backend.domain.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResult,
    CheckoutSessionStatus,
    ProviderWebhookEvent,
)
from backend.integration.payments.base import (
    PaymentProviderError,
    PaymentProviderUnavailableError,
    PaymentWebhookVerificationError,
)

TBANK_API_BASE_URL = "https://securepay.tinkoff.ru/v2"
TBANK_PAYMENT_URL_HOSTS = frozenset(
    {
        "pay.tbank.ru",
        "securepay.tinkoff.ru",
        "securepay.tbank.ru",
    }
)


class TBankPaymentProvider:
    """Hosted checkout adapter for T-Bank internet acquiring."""

    provider_name = "tbank"

    def __init__(
        self,
        *,
        terminal_key: str,
        password: SecretStr | str | None,
        backend_url: str,
        base_url: str = TBANK_API_BASE_URL,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._terminal_key = terminal_key.strip()
        self._password = _secret_value(password)
        self._backend_url = backend_url.rstrip("/")
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        if not self._terminal_key or not self._password:
            raise PaymentProviderError("T-Bank terminal key and password are required")

    async def create_checkout_session(
        self,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResult:
        """Create a T-Bank hosted checkout session from server-priced data."""
        if request.currency.upper() != "RUB":
            raise PaymentProviderError("T-Bank checkout supports only RUB prices")
        if request.amount_minor <= 0:
            raise PaymentProviderError("T-Bank checkout amount must be positive")

        order_id = uuid4().hex
        payload: dict[str, Any] = {
            "TerminalKey": self._terminal_key,
            "Amount": request.amount_minor,
            "OrderId": order_id,
            "Description": _checkout_description(request.plan_code),
            "SuccessURL": request.success_url,
            "FailURL": request.cancel_url,
            "NotificationURL": f"{self._backend_url}/v1/billing/webhooks/tbank",
        }
        payload["Token"] = _build_tbank_token(payload, self._password)

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(f"{self._base_url}/Init", json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise PaymentProviderUnavailableError(
                "T-Bank checkout provider is unavailable"
            ) from exc
        except (httpx.HTTPStatusError, json.JSONDecodeError) as exc:
            raise PaymentProviderError("T-Bank checkout provider returned an error") from exc

        if not _as_bool(data.get("Success")):
            raise PaymentProviderError("T-Bank checkout init was rejected")

        provider_payment_id = _optional_str(data.get("PaymentId"))
        payment_url = _optional_str(data.get("PaymentURL"))
        if not provider_payment_id or not payment_url:
            raise PaymentProviderError("T-Bank checkout response is incomplete")
        if not _is_allowed_payment_url(payment_url):
            raise PaymentProviderError("T-Bank checkout response has unexpected payment URL")

        return CheckoutSessionResult(
            provider=self.provider_name,
            provider_session_id=provider_payment_id,
            payment_url=payment_url,
            provider_order_id=order_id,
            status=CheckoutSessionStatus.CREATED.value,
            expires_at=_parse_datetime(data.get("RedirectDueDate")),
            provider_status=_optional_str(data.get("Status")),
            can_activate_entitlement=False,
        )

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Verify a T-Bank notification token and return a sanitized event."""
        body = _parse_webhook_payload(payload, headers)

        token = _optional_str(body.get("Token"))
        if not token:
            raise PaymentWebhookVerificationError("Missing T-Bank webhook token")
        expected_token = _build_tbank_token(body, self._password)
        if not hmac.compare_digest(token.lower(), expected_token.lower()):
            raise PaymentWebhookVerificationError("Invalid T-Bank webhook token")

        terminal_key = _optional_str(body.get("TerminalKey"))
        if terminal_key != self._terminal_key:
            raise PaymentWebhookVerificationError("Unexpected T-Bank terminal key")

        payment_id = _optional_str(body.get("PaymentId"))
        order_id = _optional_str(body.get("OrderId"))
        status = _optional_str(body.get("Status"))
        provider_event_id = _provider_event_id(payment_id, order_id, status, payload)

        return ProviderWebhookEvent(
            provider=self.provider_name,
            provider_event_id=provider_event_id,
            event_type="payment",
            payload_hash=hashlib.sha256(payload).hexdigest(),
            provider_payment_id=payment_id,
            provider_order_id=order_id,
            amount_minor=_optional_int(body.get("Amount")),
            provider_subscription_id=_optional_str(body.get("RebillId")),
            provider_status=status,
        )


def _secret_value(secret: SecretStr | str | None) -> str:
    if isinstance(secret, SecretStr):
        return secret.get_secret_value().strip()
    return (secret or "").strip()


def _parse_webhook_payload(payload: bytes, headers: dict[str, str]) -> dict[str, Any]:
    content_type = headers.get("content-type", "").lower()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PaymentWebhookVerificationError("Invalid T-Bank webhook encoding") from exc

    if "application/x-www-form-urlencoded" in content_type:
        return dict(parse_qsl(text, keep_blank_values=True))
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = dict(parse_qsl(text, keep_blank_values=True))
    if not isinstance(parsed, dict) or not parsed:
        raise PaymentWebhookVerificationError("Invalid T-Bank webhook payload")
    return parsed


def _build_tbank_token(payload: dict[str, Any], password: str) -> str:
    """Build T-Bank SHA-256 token from root scalar fields plus password."""
    token_fields: dict[str, Any] = {"Password": password}
    for key, value in payload.items():
        if key == "Token" or value is None or isinstance(value, (dict, list)):
            continue
        token_fields[key] = value
    token_source = "".join(
        _tbank_token_value(token_fields[key]) for key in sorted(token_fields)
    )
    return hashlib.sha256(token_source.encode("utf-8")).hexdigest()


def _tbank_token_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _checkout_description(plan_code: str) -> str:
    return f"EdTon.ai subscription: {plan_code}"[:140]


def _is_allowed_payment_url(payment_url: str) -> bool:
    parsed = urlparse(payment_url)
    return parsed.scheme == "https" and parsed.hostname in TBANK_PAYMENT_URL_HOSTS


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    text = _optional_str(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def _parse_datetime(value: Any) -> datetime | None:
    text = _optional_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _provider_event_id(
    payment_id: str | None,
    order_id: str | None,
    status: str | None,
    payload: bytes,
) -> str:
    if payment_id and status:
        return f"{payment_id}:{status}:{order_id or '-'}"
    return hashlib.sha256(payload).hexdigest()
