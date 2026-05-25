import uuid

import httpx
import pytest
from httpx import AsyncClient

from backend.integration.scraper.scraper import WebScraper

# Mock data for AI responses
MOCK_PARSED_RESUME = {
    "personal_info": {"name": "Test User", "title": "Developer"},
    "skills": [{"name": "Python", "category": "language"}],
    "work_experience": [{"company": "Tech Corp", "title": "Senior Dev"}],
    "education": [{"institution": "University", "degree": "BS CS"}],
}

MOCK_PARSED_VACANCY = {
    "job_title": "Senior Python Developer",
    "company": "AI Startup",
    "required_skills": [{"name": "Python"}, {"name": "FastAPI"}],
    "responsibilities": ["Write code", "Fix bugs"],
}

MOCK_MATCH_ANALYSIS = {
    "score": 85,
    "score_breakdown": {
        "skill_fit": {"value": 45, "comment": "Good skills"},
        "experience_fit": {"value": 20, "comment": "Relevant exp"},
        "ats_fit": {"value": 10, "comment": "Keywords match"},
        "clarity_evidence": {"value": 10, "comment": "Clear"},
    },
    "matched_required_skills": ["Python"],
    "missing_required_skills": ["FastAPI"],
    "matched_preferred_skills": [],
    "missing_preferred_skills": [],
    "gaps": [],
    "checkbox_options": [],
}


@pytest.mark.anyio
async def test_parse_resume_flow(client: AsyncClient, mock_ai_provider):
    """Test full resume parsing flow with mocked AI."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_RESUME

    response = await client.post(
        "/v1/resumes/parse",
        json={
            "resume_text": f"I am a developer with Python skills @ Tech Corp {uuid.uuid4()}"
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert data["parsed_resume"]["personal_info"]["name"] == "Test User"
    assert data["parsed_resume"]["skills"][0]["name"] == "Python"
    assert data["cache_hit"] is False

    # Verify AI was called
    mock_ai_provider.generate_json.assert_called_once()


@pytest.mark.anyio
async def test_get_and_update_resume_flow(client: AsyncClient, mock_ai_provider):
    """Resume detail endpoints should use service-layer persistence."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_RESUME

    parse_response = await client.post(
        "/v1/resumes/parse",
        json={"resume_text": f"Resume for detail flow {uuid.uuid4()}"},
    )
    resume_id = parse_response.json()["resume_id"]

    get_response = await client.get(f"/v1/resumes/{resume_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == resume_id

    patch_response = await client.patch(
        f"/v1/resumes/{resume_id}",
        json={"parsed_data": {"summary": "Updated summary"}},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["parsed_data"]["summary"] == "Updated summary"


@pytest.mark.anyio
async def test_parse_vacancy_flow(client: AsyncClient, mock_ai_provider):
    """Test full vacancy parsing flow with mocked AI."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_VACANCY

    response = await client.post(
        "/v1/vacancies/parse",
        json={"vacancy_text": f"We need a Python developer {uuid.uuid4()}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert data["parsed_vacancy"]["job_title"] == "Senior Python Developer"
    assert data["parsed_vacancy"]["required_skills"][0]["name"] == "Python"
    assert data["cache_hit"] is False

    # Verify AI was called
    mock_ai_provider.generate_json.assert_called_once()


@pytest.mark.anyio
async def test_parse_vacancy_url_stores_sanitized_source_url(
    client: AsyncClient,
    mock_ai_provider,
    monkeypatch,
):
    """URL imports must not persist user-controlled query secrets."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_VACANCY

    async def resolve_public_host(hostname: str, port: int) -> set[str]:
        return {"8.8.8.8"}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.hh.ru":
            return httpx.Response(403, request=request)
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

    response = await client.post(
        "/v1/vacancies/parse",
        json={"url": "http://hh.ru/vacancy/123?access_token=secret#fragment"},
    )

    assert response.status_code == 200
    vacancy_id = response.json()["vacancy_id"]
    repo = client.fake_vacancy_repo
    vacancy = await repo.get_by_id(uuid.UUID(vacancy_id))
    assert vacancy.source_url == "https://hh.ru/vacancy/123"
    assert "access_token" not in vacancy.source_url
    assert "secret" not in vacancy.source_url


@pytest.mark.anyio
async def test_parse_vacancy_mixed_input_stores_sanitized_source_url(
    client: AsyncClient,
    mock_ai_provider,
):
    """Even text-first submissions must not persist URL query secrets."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_VACANCY

    response = await client.post(
        "/v1/vacancies/parse",
        json={
            "vacancy_text": f"Manual vacancy text for mixed input {uuid.uuid4()}",
            "url": "https://hh.ru/vacancy/123?access_token=secret#fragment",
        },
    )

    assert response.status_code == 200
    vacancy_id = response.json()["vacancy_id"]
    vacancy = await client.fake_vacancy_repo.get_by_id(uuid.UUID(vacancy_id))
    assert vacancy.source_url == "https://hh.ru/vacancy/123"
    assert "access_token" not in vacancy.source_url
    assert "secret" not in vacancy.source_url


@pytest.mark.anyio
async def test_get_and_update_vacancy_flow(client: AsyncClient, mock_ai_provider):
    """Vacancy detail endpoints should use service-layer persistence."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_VACANCY

    parse_response = await client.post(
        "/v1/vacancies/parse",
        json={"vacancy_text": f"Vacancy for detail flow {uuid.uuid4()}"},
    )
    vacancy_id = parse_response.json()["vacancy_id"]

    get_response = await client.get(f"/v1/vacancies/{vacancy_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == vacancy_id

    patch_response = await client.patch(
        f"/v1/vacancies/{vacancy_id}",
        json={"parsed_data": {"job_title": "Updated title"}},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["parsed_data"]["job_title"] == "Updated title"


@pytest.mark.anyio
async def test_analyze_match_flow(client: AsyncClient, mock_ai_provider):
    """Test match analysis flow with mocked AI."""
    mock_ai_provider.generate_json.return_value = MOCK_MATCH_ANALYSIS

    # Needs a real resume and vacancy text, but we mock the AI response anyway
    payload = {
        "resume_text": f"resume content {uuid.uuid4()}",
        "vacancy_text": f"vacancy content {uuid.uuid4()}",
    }

    response = await client.post("/v1/match/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert data["analysis"]["score"] == 70
    assert data["analysis"]["matched_required_skills"] == ["Python"]
    assert data["cache_hit"] is False

    # Verify AI was called for the full pipeline:
    # 1) parse resume, 2) parse vacancy, 3) analyze match
    assert mock_ai_provider.generate_json.call_count == 3
