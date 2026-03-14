"""Tests for health check and configuration endpoints."""

import pytest


@pytest.mark.anyio
async def test_health_endpoint_returns_200(client):
    """Health check endpoint should return 200 with status info."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


@pytest.mark.anyio
async def test_health_v1_endpoint_returns_200(client):
    """V1 health check should mirror root health check."""
    response = await client.get("/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data


@pytest.mark.anyio
async def test_limits_endpoint(client):
    """Limits endpoint should return max character counts."""
    response = await client.get("/v1/limits")
    assert response.status_code == 200

    data = response.json()
    assert "max_resume_chars" in data
    assert "max_vacancy_chars" in data
    assert isinstance(data["max_resume_chars"], int)
    assert isinstance(data["max_vacancy_chars"], int)
    assert data["max_resume_chars"] > 0
    assert data["max_vacancy_chars"] > 0
