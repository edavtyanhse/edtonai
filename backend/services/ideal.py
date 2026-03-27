"""IdealResumeService - generate ideal resume template for vacancy."""

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.domain.ideal import IdealResumeResult
from backend.errors.business import VacancyNotFoundError, ValidationError
from backend.integration.ai.base import AIProvider
from backend.integration.ai.prompts import IDEAL_RESUME_PROMPT
from backend.repositories.interfaces import IIdealResumeRepository, IVacancyRepository
from backend.services.base import CachedAIService
from backend.services.interfaces import IVacancyService
from backend.services.utils import compute_hash


class IdealResumeService(CachedAIService):
    """Service for generating ideal resume template for a vacancy.

    Creates a reference example showing what an ideal candidate's resume
    would look like. Uses placeholder data, not real personal info.

    Note: caches via ``ideal_repo`` (not ``ai_result_repo``).
    """

    OPERATION = "ideal_resume"

    def __init__(
        self,
        session: AsyncSession,
        vacancy_repo: IVacancyRepository,
        ideal_repo: IIdealResumeRepository,
        vacancy_service: IVacancyService,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(
            session=session,
            ai_provider=ai_provider,
            settings=settings,
            ai_result_repo=None,  # IdealResumeService uses ideal_repo for caching
        )
        self.vacancy_repo = vacancy_repo
        self.ideal_repo = ideal_repo
        self.vacancy_service = vacancy_service

    def _compute_ideal_hash(
        self,
        parsed_vacancy: dict[str, Any],
        vacancy_hash: str,
        options: dict[str, Any],
    ) -> str:
        """Compute hash for caching ideal_resume operation.

        Hash includes:
        - Parsed vacancy JSON hash
        - Vacancy content hash
        - Options (language, template, seniority)
        """
        data = {
            "operation": self.OPERATION,
            "parsed_vacancy_hash": hashlib.sha256(
                json.dumps(parsed_vacancy, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "vacancy_hash": vacancy_hash,
            "template": options.get("template"),
            "language": options.get("language"),
            "seniority": options.get("seniority"),
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode("utf-8")
        ).hexdigest()

    async def generate_ideal(
        self,
        vacancy_text: str | None = None,
        vacancy_id: UUID | None = None,
        options: dict[str, Any] | None = None,
    ) -> IdealResumeResult:
        """Generate ideal resume for vacancy.

        Steps:
        1. Get/create VacancyRaw
        2. Get parsed_vacancy from cache
        3. Check ideal_resume cache
        4. If not cached, call LLM
        5. Save IdealResume
        6. Return result
        """
        options = options or {}

        # Step 1: Get vacancy
        if vacancy_id:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            if not vacancy:
                raise VacancyNotFoundError(str(vacancy_id))
            vacancy_text = vacancy.source_text
            vacancy_hash = vacancy.content_hash
            actual_vacancy_id = vacancy.id
        elif vacancy_text:
            vacancy_result = await self.vacancy_service.parse_and_cache(vacancy_text)
            actual_vacancy_id = vacancy_result.vacancy_id
            vacancy_hash = compute_hash(vacancy_text)
        else:
            raise ValidationError("Either vacancy_text or vacancy_id must be provided")

        # Step 2: Get parsed vacancy
        vacancy_result = await self.vacancy_service.parse_and_cache(vacancy_text)
        parsed_vacancy = vacancy_result.parsed_vacancy

        # Step 3: Check cache
        input_hash = self._compute_ideal_hash(parsed_vacancy, vacancy_hash, options)

        cached = await self.ideal_repo.get_by_input_hash(input_hash)
        if cached is not None:
            self.logger.info("Cache hit for ideal_resume: %s", input_hash[:16])
            return IdealResumeResult(
                ideal_id=cached.id,
                vacancy_id=actual_vacancy_id,
                ideal_resume_text=cached.text,
                metadata=cached.generation_metadata,
                cache_hit=True,
            )

        # Step 4: Build prompt and call LLM
        prompt = self._build_prompt(parsed_vacancy, options)

        ideal_output = await self.ai_provider.generate_json(
            prompt, prompt_name=self.OPERATION
        )

        # Step 5: Save IdealResume
        ideal = await self.ideal_repo.create(
            vacancy_id=actual_vacancy_id,
            vacancy_hash=vacancy_hash,
            text=ideal_output["ideal_resume_text"],
            generation_metadata=ideal_output.get("metadata", {}),
            options=options,
            input_hash=input_hash,
            provider=self.provider_name,
            model=self.model_name,
        )
        await self.session.commit()

        self.logger.info("Created ideal resume: %s", ideal.id)

        return IdealResumeResult(
            ideal_id=ideal.id,
            vacancy_id=actual_vacancy_id,
            ideal_resume_text=ideal_output["ideal_resume_text"],
            metadata=ideal_output.get("metadata", {}),
            cache_hit=False,
        )

    def _build_prompt(
        self,
        parsed_vacancy: dict[str, Any],
        options: dict[str, Any],
    ) -> str:
        """Build prompt for ideal_resume operation."""
        options_json = {
            "language": options.get("language", "auto"),
            "template": options.get("template", "default"),
            "seniority": options.get("seniority", "any"),
        }

        return IDEAL_RESUME_PROMPT.replace(
            "{{PARSED_VACANCY_JSON}}",
            json.dumps(parsed_vacancy, ensure_ascii=False, indent=2),
        ).replace(
            "{{IDEAL_OPTIONS_JSON}}",
            json.dumps(options_json, ensure_ascii=False, indent=2),
        )
