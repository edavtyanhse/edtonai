"""Security hardening regression tests."""

import logging

import httpx
import pytest
from starlette.requests import Request

from backend.core.config import Settings, settings
from backend.core.logging import _redact_text
from backend.errors.integration import ScraperError
from backend.integration.scraper.scraper import WebScraper
from backend.main import _client_ip, _rate_limit_rule, container
from backend.tests.integration.conftest import InMemoryResumeRepo


@pytest.mark.anyio
async def test_public_refresh_cookie_setter_is_removed(unauth_client):
    response = await unauth_client.post(
        "/auth/set-cookie?refresh_token=00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("post", "/v1/resumes/parse", {"resume_text": "x" * 20}),
        ("post", "/v1/vacancies/parse", {"vacancy_text": "x" * 20}),
        (
            "post",
            "/v1/match/analyze",
            {"resume_text": "x" * 20, "vacancy_text": "y" * 20},
        ),
        ("post", "/v1/resumes/adapt", {"resume_text": "x" * 20}),
        ("post", "/v1/resumes/ideal", {"vacancy_text": "x" * 20}),
        ("get", "/v1/versions", None),
    ],
)
async def test_sensitive_endpoints_require_auth(
    unauth_client,
    method: str,
    path: str,
    json: dict | None,
):
    if json is None:
        response = await getattr(unauth_client, method)(path)
    else:
        response = await getattr(unauth_client, method)(path, json=json)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_scraper_blocks_loopback_url():
    with pytest.raises(ScraperError):
        await WebScraper.fetch_text("http://127.0.0.1/vacancy")


@pytest.mark.anyio
async def test_scraper_blocks_unlisted_public_host_before_network():
    with pytest.raises(ScraperError, match="host is not allowed"):
        await WebScraper.fetch_text("https://example.com/vacancy")


@pytest.mark.anyio
async def test_hh_api_forbidden_falls_back_to_https_html_without_query(monkeypatch):
    requested_urls: list[str] = []

    async def resolve_public_host(hostname: str, port: int) -> set[str]:
        return {"8.8.8.8"}

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if request.url.host == "api.hh.ru":
            assert request.headers["HH-User-Agent"] == settings.hh_api_user_agent
            return httpx.Response(
                403,
                json={"errors": [{"type": "forbidden"}]},
                request=request,
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><body><h1>Бизнес-аналитик</h1><p>Описание вакансии</p></body></html>",
            request=request,
        )

    transport = httpx.MockTransport(handler)

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(WebScraper, "_resolve_host", staticmethod(resolve_public_host))
    monkeypatch.setattr(
        "backend.integration.scraper.scraper.httpx.AsyncClient",
        MockAsyncClient,
    )

    text = await WebScraper.fetch_text(
        "http://hh.ru/vacancy/123?access_token=secret",
        settings=settings,
    )

    assert "Бизнес-аналитик" in text
    assert "https://hh.ru/vacancy/123" in requested_urls
    assert all("access_token" not in url for url in requested_urls)


@pytest.mark.anyio
async def test_hh_html_legal_restriction_returns_actionable_error(monkeypatch):
    requested_urls: list[str] = []

    async def resolve_public_host(hostname: str, port: int) -> set[str]:
        return {"8.8.8.8"}

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if request.url.host == "api.hh.ru":
            return httpx.Response(403, request=request)
        return httpx.Response(451, request=request)

    transport = httpx.MockTransport(handler)

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(WebScraper, "_resolve_host", staticmethod(resolve_public_host))
    monkeypatch.setattr(
        "backend.integration.scraper.scraper.httpx.AsyncClient",
        MockAsyncClient,
    )

    with pytest.raises(ScraperError) as exc_info:
        await WebScraper.fetch_text(
            "https://hh.ru/vacancy/123?access_token=secret",
            settings=settings,
        )

    assert exc_info.value.status_code == 422
    assert "Вставьте текст вакансии вручную" in exc_info.value.message
    assert requested_urls == [
        "https://api.hh.ru/vacancies/123",
        "https://hh.ru/vacancy/123",
    ]
    assert all("access_token" not in url for url in requested_urls)


@pytest.mark.anyio
async def test_hh_api_not_found_does_not_fall_back_to_html(monkeypatch):
    requested_hosts: list[str] = []

    async def resolve_public_host(hostname: str, port: int) -> set[str]:
        return {"8.8.8.8"}

    def handler(request: httpx.Request) -> httpx.Response:
        requested_hosts.append(request.url.host or "")
        return httpx.Response(
            404,
            json={"errors": [{"type": "not_found"}]},
            request=request,
        )

    transport = httpx.MockTransport(handler)

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(WebScraper, "_resolve_host", staticmethod(resolve_public_host))
    monkeypatch.setattr(
        "backend.integration.scraper.scraper.httpx.AsyncClient",
        MockAsyncClient,
    )

    with pytest.raises(ScraperError) as exc_info:
        await WebScraper.fetch_text("https://hh.ru/vacancy/404", settings=settings)

    assert exc_info.value.status_code == 404
    assert requested_hosts == ["api.hh.ru"]


@pytest.mark.anyio
async def test_scraper_fetch_error_does_not_leak_url_query(monkeypatch, caplog):
    async def resolve_public_host(hostname: str, port: int) -> set[str]:
        return {"8.8.8.8"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, request=request)

    transport = httpx.MockTransport(handler)

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(WebScraper, "_resolve_host", staticmethod(resolve_public_host))
    monkeypatch.setattr(
        "backend.integration.scraper.scraper.httpx.AsyncClient",
        MockAsyncClient,
    )

    caplog.set_level(logging.WARNING)
    with pytest.raises(ScraperError) as exc_info:
        await WebScraper._fetch_html(
            "https://hh.ru/vacancy/123?access_token=secret",
            settings,
        )

    assert "access_token" not in exc_info.value.message
    assert "secret" not in exc_info.value.message
    assert "access_token" not in caplog.text
    assert "secret" not in caplog.text


@pytest.mark.anyio
@pytest.mark.parametrize("address", ["100.64.0.1", "169.254.169.254", "2001:db8::1"])
async def test_scraper_blocks_non_global_resolved_ips(monkeypatch, address: str):
    async def resolve_non_global_host(hostname: str, port: int) -> set[str]:
        return {address}

    monkeypatch.setattr(
        WebScraper,
        "_resolve_host",
        staticmethod(resolve_non_global_host),
    )

    with pytest.raises(ScraperError, match="Private or local network"):
        await WebScraper.fetch_text("https://hh.ru/vacancy/123", settings=settings)


def test_hh_api_user_agent_rejects_control_characters(monkeypatch):
    monkeypatch.setenv("HH_API_USER_AGENT", "EdTonAI\r\nAuthorization: secret")

    with pytest.raises(ValueError, match="HH_API_USER_AGENT"):
        Settings()


def test_production_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short")

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings()


def test_enabled_tbank_provider_requires_backend_secrets(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", "")
    monkeypatch.setenv("TBANK_PASSWORD", "")

    with pytest.raises(ValueError, match="T-Bank payments require"):
        Settings()


def test_enabled_tbank_provider_rejects_blank_secret_values(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", "terminal-test")
    monkeypatch.setenv("TBANK_PASSWORD", " ")

    with pytest.raises(ValueError, match="T-Bank payments require"):
        Settings()


def test_enabled_tbank_provider_rejects_blank_terminal_key(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", " ")
    monkeypatch.setenv("TBANK_PASSWORD", "password-test")

    with pytest.raises(ValueError, match="T-Bank payments require"):
        Settings()


def test_enabled_tbank_provider_accepts_terminal_key_and_password(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", "terminal-test")
    monkeypatch.setenv("TBANK_PASSWORD", "password-test")

    settings = Settings()

    assert settings.payment_provider == "tbank"


def test_tbank_notification_url_requires_https(monkeypatch):
    monkeypatch.setenv("TBANK_NOTIFICATION_URL", "http://example.com/webhook")

    with pytest.raises(ValueError, match="TBANK_NOTIFICATION_URL"):
        Settings()


def test_rate_limit_ip_ignores_untrusted_forwarded_for():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/auth/login",
            "headers": [(b"x-forwarded-for", b"203.0.113.10")],
            "client": ("198.51.100.20", 12345),
        }
    )

    assert _client_ip(request) == "198.51.100.20"


def test_rate_limit_ip_uses_forwarded_for_from_trusted_proxy():
    class _Config:
        trusted_proxy_ip_set = {"198.51.100.20"}

    with container.config.override(_Config()):
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/auth/login",
                "headers": [(b"x-forwarded-for", b"192.0.2.99, 203.0.113.10")],
                "client": ("198.51.100.20", 12345),
            }
        )

        assert _client_ip(request) == "203.0.113.10"


def test_payment_webhook_route_has_dedicated_rate_limit():
    category, rule = _rate_limit_rule("/v1/billing/webhooks/tbank")

    assert category == "payment_webhook"
    assert rule.max_requests == settings.payment_webhook_rate_limit_per_minute


def test_payment_log_redaction_covers_urls_tokens_and_signatures():
    message = (
        'PaymentURL: https://securepay.tinkoff.ru/new/pay_1 '
        'Token: secret-token Signature: secret-signature'
    )

    redacted = _redact_text(message)

    assert "https://securepay.tinkoff.ru" not in redacted
    assert "secret-token" not in redacted
    assert "secret-signature" not in redacted
    assert "[REDACTED]" in redacted


@pytest.mark.anyio
async def test_user_resume_patch_does_not_mutate_shared_raw_record():
    repo = InMemoryResumeRepo()
    resume = await repo.create("Shared resume", "shared-resume-hash")

    await repo.link_user_resume("11111111-1111-1111-1111-111111111111", resume.id)
    await repo.link_user_resume("22222222-2222-2222-2222-222222222222", resume.id)

    patched = await repo.update_parsed_data_for_user(
        resume.id,
        "11111111-1111-1111-1111-111111111111",
        {"summary": "User A private edit"},
    )
    other_user_view = await repo.get_by_id_for_user(
        resume.id,
        "22222222-2222-2222-2222-222222222222",
    )

    assert patched.summary == "User A private edit"
    assert other_user_view.summary is None
    assert repo.by_id[resume.id].summary is None
