"""AdaptResumeService - adapt resume for vacancy based on selected improvements."""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.factory import get_ai_provider
from backend.core.config import settings
from backend.prompts import GENERATE_UPDATED_RESUME_PROMPT
from backend.repositories import (
    ResumeRepository,
    VacancyRepository,
    AIResultRepository,
    ResumeVersionRepository,
)
from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService
from backend.services.match import MatchService
from backend.services.utils import (
    get_model_name,
    get_provider_name,
    prompt_template_sha256,
)


@dataclass
class SelectedImprovement:
    """Single improvement with optional user input."""
    checkbox_id: str
    user_input: Optional[str] = None
    ai_generate: bool = False


@dataclass
class AdaptResumeResult:
    """Result of resume adaptation."""

    version_id: UUID
    parent_version_id: Optional[UUID]
    resume_id: UUID
    vacancy_id: UUID
    updated_resume_text: str
    change_log: list[dict[str, Any]]
    applied_checkbox_ids: list[str]
    cache_hit: bool


class AdaptResumeService:
    """Service for adapting resume to vacancy requirements.

    Hybrid approach:
    - LLM returns both full text AND change_log
    - Results are cached by input hash
    - Each adaptation creates a new ResumeVersion
    """

    OPERATION = "adapt_resume"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resume_repo = ResumeRepository(session)
        self.vacancy_repo = VacancyRepository(session)
        self.ai_result_repo = AIResultRepository(session)
        self.version_repo = ResumeVersionRepository(session)
        self.resume_service = ResumeService(session)
        self.vacancy_service = VacancyService(session)
        self.match_service = MatchService(session)
        self.ai_provider = get_ai_provider(task_type="reasoning")
        self.logger = logging.getLogger(__name__)

    def _compute_adapt_hash(
        self,
        original_resume_text: str,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
        analysis: dict[str, Any],
        selected_improvements: list[SelectedImprovement],
        options: dict[str, Any],
    ) -> str:
        """Compute hash for caching adapt_resume operation.

        Hash includes:
        - Original resume text hash
        - Parsed resume JSON
        - Parsed vacancy JSON
        - Analysis JSON
        - Selected improvements (checkbox_id + user_input + ai_generate)
        - Options (language, template)
        """
        # Convert improvements to serializable format
        improvements_data = [
            {
                "checkbox_id": imp.checkbox_id,
                "user_input": imp.user_input,
                "ai_generate": imp.ai_generate,
            }
            for imp in sorted(selected_improvements, key=lambda x: x.checkbox_id)
        ]
        
        data = {
            "operation": self.OPERATION,
            "original_resume_text_hash": hashlib.sha256(
                original_resume_text.encode("utf-8")
            ).hexdigest(),
            "parsed_resume_hash": hashlib.sha256(
                json.dumps(parsed_resume, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "parsed_vacancy_hash": hashlib.sha256(
                json.dumps(parsed_vacancy, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "analysis_hash": hashlib.sha256(
                json.dumps(analysis, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "selected_improvements": improvements_data,
            "template": options.get("template"),
            "language": options.get("language"),
            "provider": get_provider_name(self.ai_provider),
            "model": get_model_name(self.ai_provider, fallback=settings.ai_model),
            "prompt_template_sha256": prompt_template_sha256(GENERATE_UPDATED_RESUME_PROMPT),
            "temperature": settings.ai_temperature,
            "max_tokens": settings.ai_max_tokens,
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode("utf-8")
        ).hexdigest()

    async def adapt_and_version(
        self,
        resume_text: Optional[str] = None,
        resume_id: Optional[UUID] = None,
        vacancy_text: Optional[str] = None,
        vacancy_id: Optional[UUID] = None,
        selected_improvements: Optional[list[SelectedImprovement]] = None,
        selected_checkbox_ids: Optional[list[str]] = None,  # Legacy support
        base_version_id: Optional[UUID] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> AdaptResumeResult:
        """Adapt resume for vacancy and create new version.

        Steps:
        1. Get/create ResumeRaw and VacancyRaw
        2. Get parsed_resume from cache
        3. Get parsed_vacancy from cache
        4. Get match_analysis from cache
        5. Check adapt_resume cache
        6. If not cached, call LLM
        7. Create ResumeVersion
        8. Return result
        """
        options = options or {}
        
        # Handle legacy format (selected_checkbox_ids) -> convert to selected_improvements
        if selected_improvements is None and selected_checkbox_ids:
            selected_improvements = [
                SelectedImprovement(checkbox_id=cid, ai_generate=True)
                for cid in selected_checkbox_ids
            ]
        selected_improvements = selected_improvements or []
        
        # Extract checkbox_ids for storing in version
        checkbox_ids_for_storage = [imp.checkbox_id for imp in selected_improvements]

        # Step 1: Get resume
        if resume_id:
            resume = await self.resume_repo.get_by_id(resume_id)
            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")
            resume_text = resume.source_text
            actual_resume_id = resume.id
        elif resume_text:
            resume_result = await self.resume_service.parse_and_cache(resume_text)
            actual_resume_id = resume_result.resume_id
        else:
            raise ValueError("Either resume_text or resume_id must be provided")

        # Step 2: Get vacancy
        if vacancy_id:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            if not vacancy:
                raise ValueError(f"Vacancy not found: {vacancy_id}")
            vacancy_text = vacancy.source_text
            actual_vacancy_id = vacancy.id
        elif vacancy_text:
            vacancy_result = await self.vacancy_service.parse_and_cache(vacancy_text)
            actual_vacancy_id = vacancy_result.vacancy_id
        else:
            raise ValueError("Either vacancy_text or vacancy_id must be provided")

        # Step 2.5: Validate base_version_id (if provided)
        if base_version_id:
            existing_version = await self.version_repo.get_by_id(base_version_id)
            if not existing_version:
                self.logger.warning(
                    "base_version_id %s not found, ignoring", base_version_id
                )
                base_version_id = None  # Reset to None if not found

        # Step 3: Get parsed resume
        resume_result = await self.resume_service.parse_and_cache(resume_text)
        parsed_resume = resume_result.parsed_resume

        # Step 4: Get parsed vacancy
        vacancy_result = await self.vacancy_service.parse_and_cache(vacancy_text)
        parsed_vacancy = vacancy_result.parsed_vacancy

        # Step 5: Get match analysis
        match_result = await self.match_service.analyze_and_cache(
            parsed_resume, parsed_vacancy
        )
        analysis = match_result.analysis
        analysis_id = match_result.analysis_id

        # Step 6: Check adapt cache
        input_hash = self._compute_adapt_hash(
            resume_text,
            parsed_resume,
            parsed_vacancy,
            analysis,
            selected_improvements,
            options,
        )

        cached_result = await self.ai_result_repo.get(self.OPERATION, input_hash)
        if cached_result is not None:
            self.logger.info("Cache hit for adapt_resume: %s", input_hash[:16])

            # Still need to create version for history
            adapt_output = cached_result.output_json
            version = await self.version_repo.create(
                resume_id=actual_resume_id,
                vacancy_id=actual_vacancy_id,
                text=adapt_output["updated_resume_text"],
                change_log=adapt_output.get("change_log", []),
                selected_checkbox_ids=checkbox_ids_for_storage,
                analysis_id=analysis_id,
                parent_version_id=base_version_id,
                provider=self.ai_provider.provider_name,
                model=get_model_name(self.ai_provider, fallback=settings.ai_model),
            )
            await self.session.commit()

            return AdaptResumeResult(
                version_id=version.id,
                parent_version_id=base_version_id,
                resume_id=actual_resume_id,
                vacancy_id=actual_vacancy_id,
                updated_resume_text=adapt_output["updated_resume_text"],
                change_log=adapt_output.get("change_log", []),
                applied_checkbox_ids=adapt_output.get("applied_checkbox_ids", []),
                cache_hit=True,
            )

        # Step 7: Build prompt and call LLM
        prompt = self._build_prompt(
            resume_text,
            parsed_resume,
            parsed_vacancy,
            analysis,
            selected_improvements,
        )

        adapt_output = await self.ai_provider.generate_json(
            prompt, prompt_name=self.OPERATION
        )

        # Step 8: Save to AIResult cache
        await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=input_hash,
            output_json=adapt_output,
            provider=self.ai_provider.provider_name,
            model=get_model_name(self.ai_provider, fallback=settings.ai_model),
        )
        self.logger.info("Saved adapt_resume to cache: %s", input_hash[:16])

        # Step 9: Create ResumeVersion
        version = await self.version_repo.create(
            resume_id=actual_resume_id,
            vacancy_id=actual_vacancy_id,
            text=adapt_output["updated_resume_text"],
            change_log=adapt_output.get("change_log", []),
            selected_checkbox_ids=checkbox_ids_for_storage,
            analysis_id=analysis_id,
            parent_version_id=base_version_id,
            provider=self.ai_provider.provider_name,
            model=get_model_name(self.ai_provider, fallback=settings.ai_model),
        )
        await self.session.commit()

        self.logger.info("Created resume version: %s", version.id)

        return AdaptResumeResult(
            version_id=version.id,
            parent_version_id=base_version_id,
            resume_id=actual_resume_id,
            vacancy_id=actual_vacancy_id,
            updated_resume_text=adapt_output["updated_resume_text"],
            change_log=adapt_output.get("change_log", []),
            applied_checkbox_ids=adapt_output.get("applied_checkbox_ids", []),
            cache_hit=False,
        )

    def _build_prompt(
        self,
        original_resume_text: str,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
        analysis: dict[str, Any],
        selected_improvements: list[SelectedImprovement],
    ) -> str:
        """Build prompt for adapt_resume operation."""
        # Convert improvements to serializable format for LLM
        improvements_data = [
            {
                "checkbox_id": imp.checkbox_id,
                "user_input": imp.user_input,
                "ai_generate": imp.ai_generate,
            }
            for imp in selected_improvements
        ]
        
        return (
            GENERATE_UPDATED_RESUME_PROMPT
            .replace("{{ORIGINAL_RESUME_TEXT}}", original_resume_text)
            .replace(
                "{{PARSED_RESUME_JSON}}",
                json.dumps(parsed_resume, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{PARSED_VACANCY_JSON}}",
                json.dumps(parsed_vacancy, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{MATCH_ANALYSIS_JSON}}",
                json.dumps(analysis, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{SELECTED_IMPROVEMENTS_JSON}}",
                json.dumps(improvements_data, ensure_ascii=False, indent=2),
            )
        )
