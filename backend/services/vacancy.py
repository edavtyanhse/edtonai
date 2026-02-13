"""Vacancy service - parse and cache vacancy text."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.factory import get_ai_provider
from backend.core.config import settings
from backend.prompts import PARSE_VACANCY_PROMPT
from backend.repositories import VacancyRepository, AIResultRepository
from backend.services.utils import (
    compute_ai_cache_key,
    compute_hash,
    get_model_name,
    get_provider_name,
    prompt_template_sha256,
)


@dataclass
class VacancyParseResult:
    """Result of vacancy parsing."""

    vacancy_id: UUID
    vacancy_hash: str
    parsed_vacancy: dict[str, Any]
    cache_hit: bool


class VacancyService:
    """Service for parsing and caching vacancies."""

    OPERATION = "parse_vacancy"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.vacancy_repo = VacancyRepository(session)
        self.ai_result_repo = AIResultRepository(session)
        self.ai_provider = get_ai_provider(task_type="parsing")
        self.logger = logging.getLogger(__name__)

    async def parse_and_cache(
        self,
        vacancy_text: str,
        source_url: str | None = None,
    ) -> VacancyParseResult:
        """Parse vacancy and cache result.

        1. Compute hash of normalized text
        2. Get or create VacancyRaw record
        3. Check AIResult cache
        4. If not cached, call LLM and save result
        5. Save parsed data to individual columns
        """
        content_hash = compute_hash(vacancy_text)
        provider_name = get_provider_name(self.ai_provider)
        model_name = get_model_name(self.ai_provider, fallback=settings.ai_model)
        prompt_sha = prompt_template_sha256(PARSE_VACANCY_PROMPT)
        ai_input_hash = compute_ai_cache_key(
            self.OPERATION,
            {
                "content_hash": content_hash,
                "provider": provider_name,
                "model": model_name,
                "prompt_sha256": prompt_sha,
                "temperature": settings.ai_temperature,
                "max_tokens": settings.ai_max_tokens,
            },
        )

        # Get or create vacancy record
        vacancy = await self.vacancy_repo.get_by_hash(content_hash)
        if vacancy is None:
            vacancy = await self.vacancy_repo.create(
                vacancy_text, content_hash, source_url=source_url,
            )
            self.logger.info("Created new vacancy record: %s", vacancy.id)
        elif source_url and not vacancy.source_url:
            # Backfill source_url if missing
            vacancy.source_url = source_url
            await self.session.flush()

        # Check cache
        cached_result = await self.ai_result_repo.get(self.OPERATION, ai_input_hash)
        if cached_result is not None:
            self.logger.info("Cache hit for vacancy parsing: %s", ai_input_hash[:16])
            
            # Update parsed columns if not set (e.g., migrated data)
            if vacancy.parsed_at is None:
                vacancy.set_parsed_data(cached_result.output_json)
                vacancy.parsed_at = datetime.utcnow()
                await self.session.flush()
            
            return VacancyParseResult(
                vacancy_id=vacancy.id,
                vacancy_hash=content_hash,
                parsed_vacancy=vacancy.get_parsed_data(),
                cache_hit=True,
            )

        # Call LLM
        prompt = PARSE_VACANCY_PROMPT.replace("{{VACANCY_TEXT}}", vacancy_text)
        parsed_json = await self.ai_provider.generate_json(prompt, prompt_name=self.OPERATION)

        # Save to cache
        await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=ai_input_hash,
            output_json=parsed_json,
            provider=provider_name,
            model=model_name,
        )
        self.logger.info("Saved parsed vacancy to cache: %s", ai_input_hash[:16])

        # Save parsed data to individual columns
        vacancy.set_parsed_data(parsed_json)
        vacancy.parsed_at = datetime.utcnow()
        await self.session.flush()

        return VacancyParseResult(
            vacancy_id=vacancy.id,
            vacancy_hash=content_hash,
            parsed_vacancy=vacancy.get_parsed_data(),
            cache_hit=False,
        )
