"""Vacancy service - parse and cache vacancy text."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.domain.mappers import get_vacancy_parsed_data, set_vacancy_parsed_data
from backend.domain.vacancy import VacancyParseResult
from backend.integration.ai.base import AIProvider
from backend.integration.ai.prompts import PARSE_VACANCY_PROMPT
from backend.repositories.interfaces import IAIResultRepository, IVacancyRepository
from backend.services.base import CachedAIService
from backend.services.utils import (
    compute_ai_cache_key,
    compute_hash,
    prompt_template_sha256,
)


class VacancyService(CachedAIService):
    """Service for parsing and caching vacancies."""

    OPERATION = "parse_vacancy"

    def __init__(
        self,
        session: AsyncSession,
        vacancy_repo: IVacancyRepository,
        ai_result_repo: IAIResultRepository,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(
            session=session,
            ai_provider=ai_provider,
            settings=settings,
            ai_result_repo=ai_result_repo,
        )
        self.vacancy_repo = vacancy_repo

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
        prompt_sha = prompt_template_sha256(PARSE_VACANCY_PROMPT)
        ai_input_hash = compute_ai_cache_key(
            self.OPERATION,
            {
                "content_hash": content_hash,
                "provider": self.provider_name,
                "model": self.model_name,
                "prompt_sha256": prompt_sha,
                "temperature": self.settings.ai_temperature,
                "max_tokens": self.settings.ai_max_tokens,
            },
        )

        # Get or create vacancy record
        vacancy = await self.vacancy_repo.get_by_hash(content_hash)
        if vacancy is None:
            vacancy = await self.vacancy_repo.create(
                vacancy_text,
                content_hash,
                source_url=source_url,
            )
            self.logger.info("Created new vacancy record: %s", vacancy.id)
        elif source_url and not vacancy.source_url:
            # Backfill source_url if missing
            vacancy.source_url = source_url
            await self.session.flush()

        # Check cache
        cached_result = await self._check_cache(ai_input_hash)
        if cached_result is not None:
            self.logger.info("Cache hit for vacancy parsing: %s", ai_input_hash[:16])

            # Update parsed columns if not set (e.g., migrated data)
            if vacancy.parsed_at is None:
                set_vacancy_parsed_data(vacancy, cached_result.output_json)
                vacancy.parsed_at = datetime.utcnow()
                await self.session.flush()

            return VacancyParseResult(
                vacancy_id=vacancy.id,
                vacancy_hash=content_hash,
                parsed_vacancy=get_vacancy_parsed_data(vacancy),
                cache_hit=True,
            )

        # Call LLM
        prompt = PARSE_VACANCY_PROMPT.replace("{{VACANCY_TEXT}}", vacancy_text)
        parsed_json = await self.ai_provider.generate_json(
            prompt, prompt_name=self.OPERATION
        )

        # Save to cache
        await self._save_to_cache(ai_input_hash, parsed_json)

        # Save parsed data to individual columns
        set_vacancy_parsed_data(vacancy, parsed_json)
        vacancy.parsed_at = datetime.utcnow()
        await self.session.flush()

        return VacancyParseResult(
            vacancy_id=vacancy.id,
            vacancy_hash=content_hash,
            parsed_vacancy=get_vacancy_parsed_data(vacancy),
            cache_hit=False,
        )
