"""Resume service - parse and cache resume text."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.domain.mappers import get_resume_parsed_data, set_resume_parsed_data
from backend.domain.resume import ResumeDetailResult, ResumeParseResult
from backend.errors.business import ResumeNotFoundError
from backend.integration.ai.base import AIProvider
from backend.integration.ai.prompts import PARSE_RESUME_PROMPT
from backend.repositories.interfaces import IAIResultRepository, IResumeRepository
from backend.services.base import CachedAIService
from backend.services.utils import (
    compute_ai_cache_key,
    compute_hash,
    prompt_template_sha256,
)


class ResumeService(CachedAIService):
    """Service for parsing and caching resumes."""

    OPERATION = "parse_resume"

    def __init__(
        self,
        session: AsyncSession,
        resume_repo: IResumeRepository,
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
        self.resume_repo = resume_repo

    async def get_detail(
        self, resume_id: UUID, user_id: str | None = None
    ) -> ResumeDetailResult:
        """Return detailed resume data by ID."""
        resume = (
            await self.resume_repo.get_by_id_for_user(resume_id, user_id)
            if user_id
            else await self.resume_repo.get_by_id(resume_id)
        )
        if resume is None:
            raise ResumeNotFoundError(str(resume_id))
        return self._to_detail_result(resume)

    async def update_parsed_data(
        self,
        resume_id: UUID,
        parsed_data: dict[str, Any],
        user_id: str | None = None,
    ) -> ResumeDetailResult:
        """Update structured resume data edited by a user."""
        resume = (
            await self.resume_repo.update_parsed_data_for_user(
                resume_id,
                user_id,
                parsed_data,
            )
            if user_id
            else await self.resume_repo.update_parsed_data(resume_id, parsed_data)
        )
        if resume is None:
            raise ResumeNotFoundError(str(resume_id))
        return self._to_detail_result(resume)

    async def parse_and_cache(
        self, resume_text: str, user_id: str | None = None
    ) -> ResumeParseResult:
        """Parse resume and cache result.

        1. Compute hash of normalized text
        2. Get or create ResumeRaw record
        3. Check AIResult cache
        4. If not cached, call LLM and save result
        5. Save parsed data to individual columns
        """
        content_hash = compute_hash(resume_text)
        prompt_sha = prompt_template_sha256(PARSE_RESUME_PROMPT)
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

        # Get or create resume record (handles race condition on duplicate hash)
        resume = await self.resume_repo.get_or_create(resume_text, content_hash)
        if user_id:
            await self.resume_repo.link_user_resume(user_id, resume.id)

        # Check cache
        cached_result = await self._check_cache(ai_input_hash)
        if cached_result is not None:
            self.logger.info("Cache hit for resume parsing: %s", ai_input_hash[:16])

            # Update parsed columns if not set (e.g., migrated data)
            if resume.parsed_at is None:
                set_resume_parsed_data(resume, cached_result.output_json)
                resume.parsed_at = datetime.utcnow()
                await self.session.flush()

            return ResumeParseResult(
                resume_id=resume.id,
                resume_hash=content_hash,
                parsed_resume=get_resume_parsed_data(resume),
                cache_hit=True,
            )

        # Call LLM
        prompt = PARSE_RESUME_PROMPT.replace("{{RESUME_TEXT}}", resume_text)
        parsed_json = await self.ai_provider.generate_json(
            prompt, prompt_name=self.OPERATION
        )

        # Save to cache
        await self._save_to_cache(ai_input_hash, parsed_json)

        # Save parsed data to individual columns
        set_resume_parsed_data(resume, parsed_json)
        resume.parsed_at = datetime.utcnow()
        await self.session.flush()

        return ResumeParseResult(
            resume_id=resume.id,
            resume_hash=content_hash,
            parsed_resume=get_resume_parsed_data(resume),
            cache_hit=False,
        )

    @staticmethod
    def _to_detail_result(resume: Any) -> ResumeDetailResult:
        return ResumeDetailResult(
            id=resume.id,
            source_text=resume.source_text,
            content_hash=resume.content_hash,
            parsed_data=get_resume_parsed_data(resume),
            created_at=resume.created_at,
            parsed_at=resume.parsed_at,
        )
