"""Unit tests for billing API boundary hardening."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.api.v1.billing import (
    _ensure_webhook_content_type,
    _read_limited_body,
)


def _request_with_body(body: bytes, content_type: bytes = b"application/json") -> Request:
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/billing/webhooks/tbank",
            "headers": [(b"content-type", content_type)],
        },
        receive,
    )


def test_webhook_rejects_unexpected_content_type():
    request = _request_with_body(b"{}", b"text/plain")

    with pytest.raises(HTTPException) as exc_info:
        _ensure_webhook_content_type(request)

    assert exc_info.value.status_code == 415


def test_webhook_allows_json_content_type_with_charset():
    request = _request_with_body(b"{}", b"application/json; charset=utf-8")

    _ensure_webhook_content_type(request)


@pytest.mark.anyio
async def test_webhook_body_size_limit_rejects_large_payload():
    request = _request_with_body(b"x" * 6)

    with pytest.raises(HTTPException) as exc_info:
        await _read_limited_body(request, max_bytes=5)

    assert exc_info.value.status_code == 413
