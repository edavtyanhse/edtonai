"""Security hardening regression tests."""

import pytest

from backend.core.config import Settings
from backend.errors.integration import ScraperError
from backend.integration.scraper.scraper import WebScraper


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


def test_production_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short")

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings()
