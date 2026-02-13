"""Resume service - parse and cache resume text."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.factory import get_ai_provider
from backend.core.config import settings
from backend.prompts import PARSE_RESUME_PROMPT
from backend.repositories import ResumeRepository, AIResultRepository
from backend.services.utils import (
    compute_ai_cache_key,
    compute_hash,
    get_model_name,
    get_provider_name,
    prompt_template_sha256,
)


@dataclass
class ResumeParseResult:
    """Result of resume parsing."""

    resume_id: UUID
    resume_hash: str
    parsed_resume: dict[str, Any]
    cache_hit: bool


class ResumeService:
    """Service for parsing and caching resumes."""

    OPERATION = "parse_resume"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resume_repo = ResumeRepository(session)
        self.ai_result_repo = AIResultRepository(session)
        self.ai_provider = get_ai_provider(task_type="parsing")
        self.logger = logging.getLogger(__name__)

    async def parse_and_cache(self, resume_text: str) -> ResumeParseResult:
        """Parse resume and cache result.

        1. Compute hash of normalized text
        2. Get or create ResumeRaw record
        3. Check AIResult cache
        4. If not cached, call LLM and save result
        5. Save parsed data to individual columns
        """
        content_hash = compute_hash(resume_text)
        provider_name = get_provider_name(self.ai_provider)
        model_name = get_model_name(self.ai_provider, fallback=settings.ai_model)
        prompt_sha = prompt_template_sha256(PARSE_RESUME_PROMPT)
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

        # Get or create resume record
        resume = await self.resume_repo.get_by_hash(content_hash)
        if resume is None:
            resume = await self.resume_repo.create(resume_text, content_hash)
            self.logger.info("Created new resume record: %s", resume.id)

        # Check cache
        cached_result = await self.ai_result_repo.get(self.OPERATION, ai_input_hash)
        if cached_result is not None:
            self.logger.info("Cache hit for resume parsing: %s", ai_input_hash[:16])
            
            # Update parsed columns if not set (e.g., migrated data)
            if resume.parsed_at is None:
                resume.set_parsed_data(cached_result.output_json)
                resume.parsed_at = datetime.utcnow()
                await self.session.flush()
            
            return ResumeParseResult(
                resume_id=resume.id,
                resume_hash=content_hash,
                parsed_resume=resume.get_parsed_data(),
                cache_hit=True,
            )

        # Call LLM
        prompt = PARSE_RESUME_PROMPT.replace("{{RESUME_TEXT}}", resume_text)
        parsed_json = await self.ai_provider.generate_json(prompt, prompt_name=self.OPERATION)

        # Save to cache
        await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=ai_input_hash,
            output_json=parsed_json,
            provider=provider_name,
            model=model_name,
        )
        self.logger.info("Saved parsed resume to cache: %s", ai_input_hash[:16])

        # Save parsed data to individual columns
        resume.set_parsed_data(parsed_json)
        resume.parsed_at = datetime.utcnow()
        await self.session.flush()

        return ResumeParseResult(
            resume_id=resume.id,
            resume_hash=content_hash,
            parsed_resume=resume.get_parsed_data(),
            cache_hit=False,
        )
