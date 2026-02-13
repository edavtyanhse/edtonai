"""CoverLetterService - generate cover letter for resume version."""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.factory import get_ai_provider
from backend.core.config import settings
from backend.prompts import COVER_LETTER_PROMPT
from backend.repositories import (
    AIResultRepository,
    ResumeVersionRepository,
    UserVersionRepository,
    VacancyRepository,
)


@dataclass
class CoverLetterResult:
    """Result of cover letter generation."""

    cover_letter_id: UUID
    resume_version_id: UUID
    vacancy_id: UUID | None
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
        provider: str,
        model: str,
        prompt_template: str,
    ) -> str:
        """Compute hash for caching cover letter generation.

        Hash includes:
        - Resume version text
        - Vacancy text
        - Match analysis JSON (sorted)
        - Provider/model (to avoid stale cache after model switch)
        - Prompt template hash (to avoid stale cache after prompt edits)
        """
        data = {
            "operation": self.OPERATION,
            "resume_version_text": resume_version_text,
            "vacancy_text": vacancy_text,
            "match_analysis": match_analysis,
            "provider": provider,
            "model": model,
            "prompt_template_sha256": hashlib.sha256(
                prompt_template.encode("utf-8", errors="replace")
            ).hexdigest(),
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    async def generate_cover_letter(
        self,
        resume_version_id: UUID,
        user_id: str | UUID,
        options: dict[str, Any] | None = None,
    ) -> CoverLetterResult:
        """Generate cover letter for resume version."""
        options = options or {}

        # Step 1: Get version (try ResumeVersion first, then UserVersion)
        resume_version = await self.version_repo.get_by_id(resume_version_id)
        is_user_version = False
        
        if not resume_version:
            # Try finding in UserVersion
            user_version_repo = UserVersionRepository(self.session)
            resume_version = await user_version_repo.get_by_id(
                resume_version_id, user_id=str(user_id)
            )
            is_user_version = True

        if not resume_version:
            raise ValueError(f"Resume version not found: {resume_version_id}")

        # Check ownership for UserVersion only (ResumeVersion doesn't have user_id in DB).
        if is_user_version and str(getattr(resume_version, "user_id", None)) != str(user_id):
            raise ValueError("Access denied: You do not own this resume version")

        # Step 2: Prepare data (vacancy text and analysis ID)
        vacancy_text = ""
        analysis_id = None
        vacancy_id = None 

        if is_user_version:
            # UserVersion path
            vacancy_text = resume_version.vacancy_text
            analysis_id = resume_version.analysis_id
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

        # Step 4: Compute hash (use the actual AI model name, not settings.ai_model)
        provider_name = getattr(self.ai_provider, "provider_name", "unknown")
        model_name = (
            getattr(self.ai_provider, "model", None)
            or getattr(self.ai_provider, "model_name", None)
            or settings.ai_model
        )

        # Use the resume text that the letter should be based on.
        # For UserVersion it's the adapted/ideal result_text; resume_text is the original input.
        resume_text = (
            cast(str, resume_version.result_text)
            if is_user_version
            else cast(str, resume_version.text)
        )

        input_hash = self._compute_cover_letter_hash(
            resume_version_text=resume_text,
            vacancy_text=vacancy_text,
            match_analysis=match_analysis,
            provider=str(provider_name),
            model=str(model_name),
            prompt_template=COVER_LETTER_PROMPT,
        )

        # Step 5: Check cache
        cached_result = await self.ai_result_repo.get(self.OPERATION, input_hash)
        if cached_result is not None:
            self.logger.info(
                "Cache hit for cover letter: %s", input_hash[:16]
            )
            output = cached_result.output_json or {}
            structure = output.get("structure") or {}
            if not isinstance(structure, dict):
                structure = {}
            return CoverLetterResult(
                cover_letter_id=cached_result.id,
                resume_version_id=resume_version_id,
                vacancy_id=vacancy_id,
                cover_letter_text=str(output.get("cover_letter_text", "")),
                structure=cast(dict[str, str], structure),
                key_points_used=list(output.get("key_points_used", [])) if isinstance(output.get("key_points_used", []), list) else [],
                alignment_notes=list(output.get("alignment_notes", [])) if isinstance(output.get("alignment_notes", []), list) else [],
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

        # Validate structure
        required_keys = ["cover_letter_text", "structure", "key_points_used", "alignment_notes"]
        missing_keys = [k for k in required_keys if k not in cover_letter_json]
        if missing_keys:
            raise ValueError(f"LLM returned incomplete JSON. Missing keys: {missing_keys}")
        structure = cover_letter_json.get("structure") or {}
        if not isinstance(structure, dict):
            raise ValueError("LLM returned invalid JSON: structure must be an object")
        for k in ("opening", "body", "closing"):
            if k not in structure:
                raise ValueError(f"LLM returned incomplete JSON. Missing structure key: {k}")

        # Step 8: Save to cache
        ai_result = await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=input_hash,
            output_json=cover_letter_json,
            provider=self.ai_provider.provider_name,
            model=model_name,
        )
        self.logger.info("Saved cover letter to cache: %s (model: %s)", input_hash[:16], model_name)

        return CoverLetterResult(
            cover_letter_id=ai_result.id,
            resume_version_id=resume_version_id,
            vacancy_id=vacancy_id,
            cover_letter_text=cover_letter_json.get("cover_letter_text", ""),
            structure=cover_letter_json.get("structure", {}),
            key_points_used=cover_letter_json.get("key_points_used", []),
            alignment_notes=cover_letter_json.get("alignment_notes", []),
            cache_hit=False,
        )
