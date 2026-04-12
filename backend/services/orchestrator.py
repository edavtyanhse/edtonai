"""Orchestrator service - coordinates full analysis pipeline."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.analysis import FullAnalysisResult
from backend.repositories.interfaces import IAnalysisRepository
from backend.services.interfaces import IMatchService, IResumeService, IVacancyService


class OrchestratorService:
    """Orchestrates the full resume-vacancy analysis pipeline."""

    def __init__(
        self,
        session: AsyncSession,
        resume_service: IResumeService,
        vacancy_service: IVacancyService,
        match_service: IMatchService,
        analysis_repo: IAnalysisRepository,
    ) -> None:
        self.session = session
        self.resume_service = resume_service
        self.vacancy_service = vacancy_service
        self.match_service = match_service
        self.analysis_repo = analysis_repo
        self.logger = logging.getLogger(__name__)

    async def run_analysis(
        self,
        resume_text: str,
        vacancy_text: str,
        original_analysis: dict[str, Any] | None = None,
        applied_checkbox_ids: list[str] | None = None,
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

        # Step 3: Analyze match (context-aware if improvements were applied)
        if original_analysis and applied_checkbox_ids:
            match_result = await self.match_service.analyze_with_context(
                resume_result.parsed_resume,
                vacancy_result.parsed_vacancy,
                original_analysis,
                applied_checkbox_ids,
            )
        else:
            match_result = await self.match_service.analyze_and_cache(
                resume_result.parsed_resume,
                vacancy_result.parsed_vacancy,
                resume_text=resume_text,
                vacancy_text=vacancy_text,
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
