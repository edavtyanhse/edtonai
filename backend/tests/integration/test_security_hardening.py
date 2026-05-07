"""Security hardening regression tests."""

import pytest

from backend.core.config import Settings
from backend.errors.integration import ScraperError
from backend.integration.scraper.scraper import WebScraper
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


def test_production_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short")

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings()


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
