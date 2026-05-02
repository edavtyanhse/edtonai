"""Vacancy service - parse and cache vacancy text."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.domain.mappers import get_vacancy_parsed_data, set_vacancy_parsed_data
from backend.domain.vacancy import VacancyDetailResult, VacancyParseResult
from backend.errors.business import VacancyNotFoundError
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

    async def get_detail(
        self, vacancy_id: UUID, user_id: str | None = None
    ) -> VacancyDetailResult:
        """Return detailed vacancy data by ID."""
        vacancy = (
            await self.vacancy_repo.get_by_id_for_user(vacancy_id, user_id)
            if user_id
            else await self.vacancy_repo.get_by_id(vacancy_id)
        )
        if vacancy is None:
            raise VacancyNotFoundError(str(vacancy_id))
        return self._to_detail_result(vacancy)

    async def update_parsed_data(
        self,
        vacancy_id: UUID,
        parsed_data: dict[str, Any],
        user_id: str | None = None,
    ) -> VacancyDetailResult:
        """Update structured vacancy data edited by a user."""
        vacancy = (
            await self.vacancy_repo.update_parsed_data_for_user(
                vacancy_id,
                user_id,
                parsed_data,
            )
            if user_id
            else await self.vacancy_repo.update_parsed_data(vacancy_id, parsed_data)
        )
        if vacancy is None:
            raise VacancyNotFoundError(str(vacancy_id))
        return self._to_detail_result(vacancy)

    async def parse_and_cache(
        self,
        vacancy_text: str,
        source_url: str | None = None,
        user_id: str | None = None,
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
        if user_id:
            await self.vacancy_repo.link_user_vacancy(user_id, vacancy.id)

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

    @staticmethod
    def _to_detail_result(vacancy: Any) -> VacancyDetailResult:
        return VacancyDetailResult(
            id=vacancy.id,
            source_text=vacancy.source_text,
            content_hash=vacancy.content_hash,
            parsed_data=get_vacancy_parsed_data(vacancy),
            created_at=vacancy.created_at,
            parsed_at=vacancy.parsed_at,
        )
