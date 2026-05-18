"""Security hardening regression tests."""

import pytest
from starlette.requests import Request

from backend.core.config import Settings
from backend.errors.integration import ScraperError
from backend.integration.scraper.scraper import WebScraper
from backend.main import _client_ip, container
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


def test_production_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short")

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings()


def test_enabled_tbank_provider_requires_backend_secrets(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.delenv("TBANK_TERMINAL_KEY", raising=False)
    monkeypatch.delenv("TBANK_PASSWORD", raising=False)
    monkeypatch.delenv("TBANK_WEBHOOK_SECRET", raising=False)

    with pytest.raises(ValueError, match="T-Bank payments require"):
        Settings()


def test_enabled_tbank_provider_rejects_blank_secret_values(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", "terminal-test")
    monkeypatch.setenv("TBANK_PASSWORD", " ")
    monkeypatch.setenv("TBANK_WEBHOOK_SECRET", "")

    with pytest.raises(ValueError, match="T-Bank payments require"):
        Settings()


def test_enabled_tbank_provider_rejects_blank_terminal_key(monkeypatch):
    monkeypatch.setenv("PAYMENT_PROVIDER", "tbank")
    monkeypatch.setenv("TBANK_TERMINAL_KEY", " ")
    monkeypatch.setenv("TBANK_PASSWORD", "password-test")
    monkeypatch.setenv("TBANK_WEBHOOK_SECRET", "webhook-test")

    with pytest.raises(ValueError, match="T-Bank payments require"):
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
