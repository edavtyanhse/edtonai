"""Unit tests for services — pure logic with mock repositories.

No database, no HTTP, no real AI. All dependencies are mock objects.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.match import MatchService
from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService

# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def mock_settings():
    """Minimal Settings mock."""
    s = MagicMock()
    s.ai_model = "mock-model"
    s.ai_temperature = 0.0
    s.ai_max_tokens = 4096
    return s


@pytest.fixture
def mock_ai_provider():
    """AsyncMock AI provider."""
    provider = AsyncMock()
    provider.provider_name = "mock-provider"
    provider.model = "mock-model"
    return provider


@pytest.fixture
def mock_session():
    """AsyncMock SQLAlchemy session."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_ai_result_repo():
    """AsyncMock AIResult repository."""
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    saved = MagicMock()
    saved.id = uuid.uuid4()
    repo.save = AsyncMock(return_value=saved)
    return repo


# ── ResumeService ─────────────────────────────────────────────────


class TestResumeService:
    """Unit tests for ResumeService."""

    @pytest.fixture
    def mock_resume_repo(self):
        repo = AsyncMock()
        resume = MagicMock()
        resume.id = uuid.uuid4()
        resume.parsed_at = None
        resume.personal_info = None
        resume.summary = None
        resume.skills = []
        resume.work_experience = []
        resume.education = []
        resume.certifications = []
        resume.languages = []
        resume.raw_sections = {}
        repo.get_by_hash = AsyncMock(return_value=None)
        repo.create = AsyncMock(return_value=resume)
        return repo

    @pytest.fixture
    def service(
        self, mock_session, mock_resume_repo, mock_ai_result_repo, mock_ai_provider, mock_settings,
    ):
        return ResumeService(
            session=mock_session,
            resume_repo=mock_resume_repo,
            ai_result_repo=mock_ai_result_repo,
            ai_provider=mock_ai_provider,
            settings=mock_settings,
        )

    @pytest.mark.anyio
    async def test_parse_calls_ai_on_cache_miss(
        self, service, mock_ai_provider, mock_ai_result_repo,
    ):
        """When cache is empty, AI provider should be called."""
        mock_ai_provider.generate_json.return_value = {
            "personal_info": {"name": "Test"},
            "skills": [],
        }

        result = await service.parse_and_cache("My resume text")

        assert result.cache_hit is False
        mock_ai_provider.generate_json.assert_called_once()
        mock_ai_result_repo.save.assert_called_once()

    @pytest.mark.anyio
    async def test_parse_returns_cached_on_hit(
        self, service, mock_ai_provider, mock_ai_result_repo, mock_resume_repo,
    ):
        """When cache has a result, AI provider should NOT be called."""
        cached = MagicMock()
        cached.output_json = {
            "personal_info": {"name": "Cached"},
            "skills": [{"name": "Python"}],
        }
        mock_ai_result_repo.get.return_value = cached

        # Ensure resume already exists
        resume = MagicMock()
        resume.id = uuid.uuid4()
        resume.parsed_at = None
        resume.personal_info = None
        resume.summary = None
        resume.skills = []
        resume.work_experience = []
        resume.education = []
        resume.certifications = []
        resume.languages = []
        resume.raw_sections = {}
        mock_resume_repo.get_by_hash.return_value = resume

        result = await service.parse_and_cache("My resume text")

        assert result.cache_hit is True
        mock_ai_provider.generate_json.assert_not_called()


# ── VacancyService ────────────────────────────────────────────────


class TestVacancyService:
    """Unit tests for VacancyService."""

    @pytest.fixture
    def mock_vacancy_repo(self):
        repo = AsyncMock()
        vacancy = MagicMock()
        vacancy.id = uuid.uuid4()
        vacancy.parsed_at = None
        vacancy.source_url = None
        vacancy.job_title = None
        vacancy.company = None
        vacancy.employment_type = None
        vacancy.location = None
        vacancy.required_skills = []
        vacancy.preferred_skills = []
        vacancy.experience_requirements = None
        vacancy.responsibilities = []
        vacancy.ats_keywords = []
        repo.get_by_hash = AsyncMock(return_value=None)
        repo.create = AsyncMock(return_value=vacancy)
        return repo

    @pytest.fixture
    def service(
        self, mock_session, mock_vacancy_repo, mock_ai_result_repo, mock_ai_provider, mock_settings,
    ):
        return VacancyService(
            session=mock_session,
            vacancy_repo=mock_vacancy_repo,
            ai_result_repo=mock_ai_result_repo,
            ai_provider=mock_ai_provider,
            settings=mock_settings,
        )

    @pytest.mark.anyio
    async def test_parse_calls_ai_on_cache_miss(
        self, service, mock_ai_provider, mock_ai_result_repo,
    ):
        mock_ai_provider.generate_json.return_value = {
            "job_title": "Developer",
            "company": "ACME",
        }

        result = await service.parse_and_cache("Job posting text")

        assert result.cache_hit is False
        mock_ai_provider.generate_json.assert_called_once()
        mock_ai_result_repo.save.assert_called_once()

    @pytest.mark.anyio
    async def test_parse_returns_cached_on_hit(
        self, service, mock_ai_provider, mock_ai_result_repo, mock_vacancy_repo,
    ):
        cached = MagicMock()
        cached.output_json = {
            "job_title": "Cached Job",
            "required_skills": [],
        }
        mock_ai_result_repo.get.return_value = cached

        vacancy = MagicMock()
        vacancy.id = uuid.uuid4()
        vacancy.parsed_at = None
        vacancy.job_title = None
        vacancy.company = None
        vacancy.employment_type = None
        vacancy.location = None
        vacancy.required_skills = []
        vacancy.preferred_skills = []
        vacancy.experience_requirements = None
        vacancy.responsibilities = []
        vacancy.ats_keywords = []
        mock_vacancy_repo.get_by_hash.return_value = vacancy

        result = await service.parse_and_cache("Job posting text")

        assert result.cache_hit is True
        mock_ai_provider.generate_json.assert_not_called()


# ── MatchService ──────────────────────────────────────────────────


class TestMatchService:
    """Unit tests for MatchService."""

    @pytest.fixture
    def service(
        self, mock_session, mock_ai_result_repo, mock_ai_provider, mock_settings,
    ):
        return MatchService(
            session=mock_session,
            ai_result_repo=mock_ai_result_repo,
            ai_provider=mock_ai_provider,
            settings=mock_settings,
        )

    @pytest.mark.anyio
    async def test_analyze_calls_ai_on_cache_miss(
        self, service, mock_ai_provider, mock_ai_result_repo,
    ):
        mock_ai_provider.generate_json.return_value = {
            "score": 80,
            "score_breakdown": {},
            "matched_required_skills": ["Python"],
        }

        result = await service.analyze_and_cache(
            parsed_resume={"skills": [{"name": "Python"}]},
            parsed_vacancy={"required_skills": [{"name": "Python"}]},
        )

        assert result.cache_hit is False
        mock_ai_provider.generate_json.assert_called_once()

    @pytest.mark.anyio
    async def test_analyze_returns_cached_on_hit(
        self, service, mock_ai_provider, mock_ai_result_repo,
    ):
        cached = MagicMock()
        cached.id = uuid.uuid4()
        cached.output_json = {"score": 90, "score_breakdown": {}}
        mock_ai_result_repo.get.return_value = cached

        result = await service.analyze_and_cache(
            parsed_resume={"skills": []},
            parsed_vacancy={"required_skills": []},
        )

        assert result.cache_hit is True
        assert result.analysis["score"] == 90
        mock_ai_provider.generate_json.assert_not_called()

    def test_clamp_scores_limits_values(self):
        """Score clamping should cap each category to its max."""
        raw = {
            "score": 200,
            "score_breakdown": {
                "skill_fit": {"value": 60, "comment": "Over"},
                "experience_fit": {"value": 30, "comment": "Over"},
                "ats_fit": {"value": 20, "comment": "Over"},
                "clarity_evidence": {"value": 15, "comment": "Over"},
            },
        }
        clamped = MatchService._clamp_scores(raw)

        assert clamped["score_breakdown"]["skill_fit"]["value"] == 50
        assert clamped["score_breakdown"]["experience_fit"]["value"] == 25
        assert clamped["score_breakdown"]["ats_fit"]["value"] == 15
        assert clamped["score_breakdown"]["clarity_evidence"]["value"] == 10
        assert clamped["score"] == 100  # 50+25+15+10

    def test_clamp_scores_no_change_when_within_limits(self):
        """Score clamping should not modify values within limits."""
        raw = {
            "score": 70,
            "score_breakdown": {
                "skill_fit": {"value": 35, "comment": "OK"},
                "experience_fit": {"value": 20, "comment": "OK"},
                "ats_fit": {"value": 10, "comment": "OK"},
                "clarity_evidence": {"value": 5, "comment": "OK"},
            },
        }
        clamped = MatchService._clamp_scores(raw)

        assert clamped["score_breakdown"]["skill_fit"]["value"] == 35
        assert clamped["score"] == 70  # 35+20+10+5
