"""Unit tests for T-Bank hosted checkout adapter."""

from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from backend.domain.billing import CheckoutSessionRequest, CheckoutSessionStatus
from backend.integration.payments.tbank import (
    TBankPaymentProvider,
    _build_tbank_token,
)


def test_tbank_token_matches_documented_init_example():
    payload = {
        "TerminalKey": "MerchantTerminalKey",
        "Amount": "19200",
        "OrderId": "00000",
        "Description": "Подарочная карта на 1000 рублей",
        "DATA": {"Email": "a@test.com"},
        "Receipt": {"Items": []},
    }

    assert _build_tbank_token(payload, "11111111111111") == (
        "72dd466f8ace0a37a1f740ce5fb78101712bc0665d91a8108c7c8a0ccd426db2"
    )


@pytest.mark.anyio
async def test_tbank_checkout_uses_server_controlled_payload(monkeypatch):
    captured_payloads: list[dict] = []

    class MockAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json):
            captured_payloads.append(json)
            return httpx.Response(
                200,
                json={
                    "Success": True,
                    "Status": "NEW",
                    "PaymentId": "123456789",
                    "PaymentURL": "https://securepay.tinkoff.ru/new/123456789",
                },
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(
        "backend.integration.payments.tbank.httpx.AsyncClient",
        MockAsyncClient,
    )
    provider = TBankPaymentProvider(
        terminal_key="terminal-test",
        password=SecretStr("password-test"),
        backend_url="https://api.example.com",
    )

    result = await provider.create_checkout_session(
        CheckoutSessionRequest(
            user_id=uuid4(),
            plan_code="basic",
            amount_minor=49000,
            currency="RUB",
            success_url="https://app.example.com/billing/success",
            cancel_url="https://app.example.com/billing/cancel",
        )
    )

    assert result.provider == "tbank"
    assert result.provider_session_id == "123456789"
    assert result.status == CheckoutSessionStatus.CREATED.value
    assert result.can_activate_entitlement is False
    payload = captured_payloads[0]
    assert result.provider_order_id == payload["OrderId"]
    assert payload["TerminalKey"] == "terminal-test"
    assert payload["Amount"] == 49000
    assert payload["NotificationURL"] == (
        "https://api.example.com/v1/billing/webhooks/tbank"
    )
    assert "DATA" not in payload
    assert payload["Token"]


@pytest.mark.anyio
async def test_tbank_webhook_verifies_token_and_sanitizes_event():
    provider = TBankPaymentProvider(
        terminal_key="terminal-test",
        password=SecretStr("password-test"),
        backend_url="https://api.example.com",
    )
    payload = {
        "TerminalKey": "terminal-test",
        "OrderId": "order-1",
        "Success": True,
        "Status": "CONFIRMED",
        "PaymentId": "pay-1",
        "ErrorCode": "0",
        "Amount": 49000,
        "Pan": "200000******0000",
    }
    payload["Token"] = _build_tbank_token(payload, "password-test")

    event = await provider.verify_webhook(
        json.dumps(payload).encode("utf-8"),
        headers={},
    )

    assert event.provider == "tbank"
    assert event.provider_event_id == "pay-1:CONFIRMED:order-1"
    assert event.provider_payment_id == "pay-1"
    assert event.provider_order_id == "order-1"
    assert event.amount_minor == 49000
    assert event.provider_status == "CONFIRMED"


@pytest.mark.anyio
async def test_tbank_webhook_rejects_invalid_token():
    provider = TBankPaymentProvider(
        terminal_key="terminal-test",
        password=SecretStr("password-test"),
        backend_url="https://api.example.com",
    )
    payload = {
        "TerminalKey": "terminal-test",
        "OrderId": "order-1",
        "Success": True,
        "Status": "CONFIRMED",
        "PaymentId": "pay-1",
        "Token": "bad",
    }

    with pytest.raises(Exception, match="Invalid T-Bank webhook token"):
        await provider.verify_webhook(json.dumps(payload).encode("utf-8"), headers={})


@pytest.mark.anyio
async def test_tbank_webhook_accepts_form_encoded_payload():
    provider = TBankPaymentProvider(
        terminal_key="terminal-test",
        password=SecretStr("password-test"),
        backend_url="https://api.example.com",
    )
    payload = {
        "TerminalKey": "terminal-test",
        "OrderId": "order-1",
        "Success": "true",
        "Status": "AUTHORIZED",
        "PaymentId": "pay-1",
        "ErrorCode": "0",
        "Amount": "49000",
    }
    payload["Token"] = _build_tbank_token(payload, "password-test")
    encoded = "&".join(f"{key}={value}" for key, value in payload.items())

    event = await provider.verify_webhook(
        encoded.encode("utf-8"),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert event.provider_event_id == "pay-1:AUTHORIZED:order-1"
    assert event.provider_order_id == "order-1"
    assert event.amount_minor == 49000
