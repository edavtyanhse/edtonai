"""Tests for API request validation and error handling."""

import pytest


@pytest.mark.anyio
async def test_resume_parse_rejects_empty_body(client):
    """Resume parse should reject request without required fields."""
    response = await client.post("/v1/resumes/parse", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_vacancy_parse_rejects_empty_body(client):
    """Vacancy parse should reject request without required fields."""
    response = await client.post("/v1/vacancies/parse", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_match_analyze_rejects_empty_body(client):
    """Match analyze should reject request without required fields."""
    response = await client.post("/v1/match/analyze", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_nonexistent_route_returns_404(client):
    """Requesting an unknown route should return 404."""
    response = await client.get("/v1/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_openapi_schema_available(client):
    """OpenAPI schema (Swagger) should be accessible."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert data["info"]["title"] == "Resume Adapter API"
    assert "paths" in data
    # Verify key endpoints are documented
    assert any("/resumes" in path for path in data["paths"])
    assert any("/vacancies" in path for path in data["paths"])
    assert any("/match" in path for path in data["paths"])


@pytest.mark.anyio
async def test_docs_available(client):
    """Swagger UI docs should be accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200
