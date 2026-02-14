"""Orchestrator service - coordinates full analysis pipeline."""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories import AnalysisRepository
from backend.services.match import MatchService
from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService


@dataclass
class FullAnalysisResult:
    """Result of full analysis pipeline."""

    resume_id: UUID
    vacancy_id: UUID
    analysis_id: UUID
    parsed_resume: dict[str, Any]
    parsed_vacancy: dict[str, Any]
    analysis: dict[str, Any]
    cache_hit: bool  # True if ALL results were from cache


class OrchestratorService:
    """Orchestrates the full resume-vacancy analysis pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resume_service = ResumeService(session)
        self.vacancy_service = VacancyService(session)
        self.match_service = MatchService(session)
        self.analysis_repo = AnalysisRepository(session)
        self.logger = logging.getLogger(__name__)

    async def run_analysis(
        self,
        resume_text: str,
        vacancy_text: str,
    ) -> FullAnalysisResult:
        """Run full analysis pipeline.

        1. Parse resume (with cache)
        2. Parse vacancy (with cache)
        3. Analyze match (with cache)
        4. Create AnalysisLink
        """
        # Step 1: Parse resume
        resume_result = await self.resume_service.parse_and_cache(resume_text)
        self.logger.info(
            "Resume parsed: id=%s cache_hit=%s",
            resume_result.resume_id,
            resume_result.cache_hit,
        )

        # Step 2: Parse vacancy
        vacancy_result = await self.vacancy_service.parse_and_cache(vacancy_text)
        self.logger.info(
            "Vacancy parsed: id=%s cache_hit=%s",
            vacancy_result.vacancy_id,
            vacancy_result.cache_hit,
        )

        # Step 3: Analyze match
        match_result = await self.match_service.analyze_and_cache(
            resume_result.parsed_resume,
            vacancy_result.parsed_vacancy,
        )
        self.logger.info(
            "Match analyzed: id=%s cache_hit=%s",
            match_result.analysis_id,
            match_result.cache_hit,
        )

        # Step 4: Create analysis link
        await self.analysis_repo.link(
            resume_id=resume_result.resume_id,
            vacancy_id=vacancy_result.vacancy_id,
            analysis_result_id=match_result.analysis_id,
        )

        # All cache hits?
        all_cache_hit = (
            resume_result.cache_hit
            and vacancy_result.cache_hit
            and match_result.cache_hit
        )

        return FullAnalysisResult(
            resume_id=resume_result.resume_id,
            vacancy_id=vacancy_result.vacancy_id,
            analysis_id=match_result.analysis_id,
            parsed_resume=resume_result.parsed_resume,
            parsed_vacancy=vacancy_result.parsed_vacancy,
            analysis=match_result.analysis,
            cache_hit=all_cache_hit,
        )
