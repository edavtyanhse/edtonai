"""CoverLetterService - generate cover letter for resume version."""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.factory import get_ai_provider
from backend.core.config import settings
from backend.prompts import COVER_LETTER_PROMPT
from backend.repositories import (
    AIResultRepository,
    ResumeVersionRepository,
    VacancyRepository,
)


@dataclass
class CoverLetterResult:
    """Result of cover letter generation."""

    cover_letter_id: UUID
    resume_version_id: UUID
    vacancy_id: UUID
    cover_letter_text: str
    structure: dict[str, str]
    key_points_used: list[str]
    alignment_notes: list[str]
    cache_hit: bool


class CoverLetterService:
    """Service for generating cover letter based on resume version.

    Generates professional cover letter that:
    - Uses only data from specific resume_version
    - Aligns with vacancy requirements
    - Addresses gaps identified in match analysis
    - Uses cached results when possible
    """

    OPERATION = "generate_cover_letter"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.ai_result_repo = AIResultRepository(session)
        self.version_repo = ResumeVersionRepository(session)
        self.vacancy_repo = VacancyRepository(session)
        self.ai_provider = get_ai_provider(task_type="reasoning")
        self.logger = logging.getLogger(__name__)

    def _compute_cover_letter_hash(
        self,
        resume_version_text: str,
        vacancy_text: str,
        match_analysis: dict[str, Any],
    ) -> str:
        """Compute hash for caching cover letter generation.

        Hash includes:
        - Resume version text
        - Vacancy text
        - Match analysis JSON (sorted)
        """
        data = {
            "operation": self.OPERATION,
            "resume_version_text": resume_version_text,
            "vacancy_text": vacancy_text,
            "match_analysis": match_analysis,
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    async def generate_cover_letter(
        self,
        resume_version_id: UUID,
        options: dict[str, Any] | None = None,
    ) -> CoverLetterResult:
        """Generate cover letter for resume version.

        Steps:
        1. Get resume_version
        2. Get vacancy
        3. Get match analysis (from analysis_id)
        4. Compute input_hash
        5. Check cache
        6. If not cached, call LLM
        7. Save to ai_result
        8. Return structured result

        Args:
            resume_version_id: ID of the resume version
            options: Optional generation options (currently unused, for future)

        Returns:
            CoverLetterResult with generated text and metadata

        Raises:
            ValueError: If resume_version, vacancy, or analysis not found
        """
        options = options or {}

        # Step 1: Get version (try ResumeVersion first, then UserVersion)
        resume_version = await self.version_repo.get_by_id(resume_version_id)
        is_user_version = False
        
        if not resume_version:
            # Try finding in UserVersion
            from backend.repositories import UserVersionRepository
            user_version_repo = UserVersionRepository(self.session)
            resume_version = await user_version_repo.get_by_id(resume_version_id)
            is_user_version = True

        if not resume_version:
             raise ValueError(f"Resume version not found: {resume_version_id}")

        # Step 2: Prepare data (vacancy text and analysis ID)
        vacancy_text = ""
        analysis_id = None
        vacancy_id = None # Initialize vacancy_id for CoverLetterResult

        if is_user_version:
            # UserVersion path
            vacancy_text = resume_version.vacancy_text
            analysis_id = resume_version.analysis_id
            # UserVersion does not have a direct vacancy_id, so we'll use None or a placeholder
            vacancy_id = None 
        else:
            # ResumeVersion path
            vacancy = await self.vacancy_repo.get_by_id(resume_version.vacancy_id)
            if not vacancy:
                raise ValueError(f"Vacancy not found: {resume_version.vacancy_id}")
            vacancy_text = vacancy.source_text
            analysis_id = resume_version.analysis_id
            vacancy_id = vacancy.id

        if not analysis_id:
             raise ValueError(
                f"Version {resume_version_id} has no analysis_id. "
                "Cannot generate cover letter without match analysis."
            )

        # Step 3: Get match analysis
        analysis_result = await self.ai_result_repo.get_by_id(analysis_id)
        if not analysis_result:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        match_analysis = analysis_result.output_json

        # Step 4: Compute hash
        resume_text = resume_version.resume_text if is_user_version else resume_version.text
        
        input_hash = self._compute_cover_letter_hash(
            resume_version_text=resume_text,
            vacancy_text=vacancy_text,
            match_analysis=match_analysis,
        )

        # Step 5: Check cache
        cached_result = await self.ai_result_repo.get(self.OPERATION, input_hash)
        if cached_result is not None:
            self.logger.info(
                "Cache hit for cover letter: %s", input_hash[:16]
            )
            output = cached_result.output_json
            return CoverLetterResult(
                cover_letter_id=cached_result.id,
                resume_version_id=resume_version_id,
                vacancy_id=vacancy.id,
                cover_letter_text=output["cover_letter_text"],
                structure=output["structure"],
                key_points_used=output["key_points_used"],
                alignment_notes=output["alignment_notes"],
                cache_hit=True,
            )

        # Step 6: Build prompt
        prompt = COVER_LETTER_PROMPT.replace(
            "{{RESUME_TEXT}}", resume_text
        ).replace(
            "{{VACANCY_TEXT}}", vacancy_text
        ).replace(
            "{{MATCH_ANALYSIS_JSON}}",
            json.dumps(match_analysis, ensure_ascii=False, indent=2),
        )

        # Step 7: Call LLM
        self.logger.info(
            "Generating cover letter for version %s", resume_version_id
        )
        cover_letter_json = await self.ai_provider.generate_json(
            prompt, prompt_name=self.OPERATION
        )

        # Step 8: Save to cache
        ai_result = await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=input_hash,
            output_json=cover_letter_json,
            provider=self.ai_provider.provider_name,
            model=settings.ai_model,
        )
        self.logger.info("Saved cover letter to cache: %s", input_hash[:16])

        return CoverLetterResult(
            cover_letter_id=ai_result.id,
            resume_version_id=resume_version_id,
            vacancy_id=vacancy.id,
            cover_letter_text=cover_letter_json["cover_letter_text"],
            structure=cover_letter_json["structure"],
            key_points_used=cover_letter_json["key_points_used"],
            alignment_notes=cover_letter_json["alignment_notes"],
            cache_hit=False,
        )
