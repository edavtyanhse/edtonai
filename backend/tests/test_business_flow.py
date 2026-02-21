import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
import uuid

# Mock data for AI responses
MOCK_PARSED_RESUME = {
    "personal_info": {"name": "Test User", "title": "Developer"},
    "skills": [{"name": "Python", "category": "language"}],
    "work_experience": [{"company": "Tech Corp", "title": "Senior Dev"}],
    "education": [{"institution": "University", "degree": "BS CS"}]
}

MOCK_PARSED_VACANCY = {
    "job_title": "Senior Python Developer",
    "company": "AI Startup",
    "required_skills": [{"name": "Python"}, {"name": "FastAPI"}],
    "responsibilities": ["Write code", "Fix bugs"]
}

MOCK_MATCH_ANALYSIS = {
    "score": 85,
    "score_breakdown": {
        "skill_fit": {"value": 45, "comment": "Good skills"},
        "experience_fit": {"value": 20, "comment": "Relevant exp"},
        "ats_fit": {"value": 10, "comment": "Keywords match"},
        "clarity_evidence": {"value": 10, "comment": "Clear"}
    },
    "matched_required_skills": ["Python"],
    "missing_required_skills": ["FastAPI"],
    "matched_preferred_skills": [],
    "missing_preferred_skills": [],
    "gaps": [],
    "checkbox_options": []
}

@pytest.fixture
def mock_ai_provider():
    provider = AsyncMock()
    provider.generate_json.side_effect = None # Reset side effect
    provider.provider_name = "mock-provider"
    provider.model = "mock-model"
    return provider

@pytest.mark.anyio
async def test_parse_resume_flow(client: AsyncClient, mock_ai_provider):
    """Test full resume parsing flow with mocked AI."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_RESUME
    
    # Patch get_ai_provider in resume service
    with patch("backend.services.resume.get_ai_provider", return_value=mock_ai_provider):
        response = await client.post(
            "/v1/resumes/parse",
            json={"resume_text": f"I am a developer with Python skills @ Tech Corp {uuid.uuid4()}"}
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
async def test_parse_vacancy_flow(client: AsyncClient, mock_ai_provider):
    """Test full vacancy parsing flow with mocked AI."""
    mock_ai_provider.generate_json.return_value = MOCK_PARSED_VACANCY
    
    # Patch get_ai_provider in vacancy service
    with patch("backend.services.vacancy.get_ai_provider", return_value=mock_ai_provider):
        response = await client.post(
            "/v1/vacancies/parse",
            json={"vacancy_text": f"We need a Python developer {uuid.uuid4()}"}
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
async def test_analyze_match_flow(client: AsyncClient, mock_ai_provider):
    """Test match analysis flow with mocked AI."""
    mock_ai_provider.generate_json.return_value = MOCK_MATCH_ANALYSIS
    
    # Needs a real resume and vacancy text, but we mock the AI response anyway
    payload = {
        "resume_text": f"resume content {uuid.uuid4()}",
        "vacancy_text": f"vacancy content {uuid.uuid4()}"
    }
    
    # Patch get_ai_provider in match service
    with patch("backend.services.match.get_ai_provider", return_value=mock_ai_provider):
        response = await client.post(
            "/v1/match/analyze",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["analysis"]["score"] == 85
        assert data["analysis"]["matched_required_skills"] == ["Python"]
        assert data["cache_hit"] is False
        
        # Verify AI was called
        mock_ai_provider.generate_json.assert_called_once()
