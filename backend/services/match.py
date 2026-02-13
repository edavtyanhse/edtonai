"""Match service - analyze resume-vacancy match and cache result."""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.factory import get_ai_provider
from backend.core.config import settings
from backend.prompts import ANALYZE_MATCH_PROMPT
from backend.repositories import AIResultRepository
from backend.services.utils import (
    compute_ai_cache_key,
    get_model_name,
    get_provider_name,
    prompt_template_sha256,
)


@dataclass
class MatchAnalysisResult:
    """Result of match analysis."""

    analysis_id: UUID
    analysis: dict[str, Any]
    cache_hit: bool


class MatchService:
    """Service for analyzing resume-vacancy match."""

    OPERATION = "analyze_match"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.ai_result_repo = AIResultRepository(session)
        self.ai_provider = get_ai_provider(task_type="reasoning")
        self.logger = logging.getLogger(__name__)

    def _compute_match_hash(
        self,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
    ) -> str:
        """Compute hash from parsed resume and vacancy JSONs."""
        combined = json.dumps(parsed_resume, sort_keys=True) + json.dumps(
            parsed_vacancy, sort_keys=True
        )
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    async def analyze_and_cache(
        self,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
    ) -> MatchAnalysisResult:
        """Analyze match and cache result.

        1. Compute hash from both parsed JSONs
        2. Check AIResult cache
        3. If not cached, call LLM and save result
        """
        base_hash = self._compute_match_hash(parsed_resume, parsed_vacancy)
        provider_name = get_provider_name(self.ai_provider)
        model_name = get_model_name(self.ai_provider, fallback=settings.ai_model)
        prompt_sha = prompt_template_sha256(ANALYZE_MATCH_PROMPT)
        input_hash = compute_ai_cache_key(
            self.OPERATION,
            {
                "base_hash": base_hash,
                "provider": provider_name,
                "model": model_name,
                "prompt_sha256": prompt_sha,
                "temperature": settings.ai_temperature,
                "max_tokens": settings.ai_max_tokens,
            },
        )

        # Check cache
        cached_result = await self.ai_result_repo.get(self.OPERATION, input_hash)
        if cached_result is not None:
            self.logger.info("Cache hit for match analysis: %s", input_hash[:16])
            return MatchAnalysisResult(
                analysis_id=cached_result.id,
                analysis=cached_result.output_json,
                cache_hit=True,
            )

        # Build prompt
        prompt = ANALYZE_MATCH_PROMPT.replace(
            "{{PARSED_RESUME_JSON}}", json.dumps(parsed_resume, ensure_ascii=False, indent=2)
        ).replace(
            "{{PARSED_VACANCY_JSON}}", json.dumps(parsed_vacancy, ensure_ascii=False, indent=2)
        )

        # Call LLM
        analysis_json = await self.ai_provider.generate_json(prompt, prompt_name=self.OPERATION)

        # Bug fix: Clamp scores to max values to prevent 12/10 capability
        if "score_breakdown" in analysis_json:
            sb = analysis_json["score_breakdown"]
            # Max values: skill_fit=50, experience_fit=25, ats_fit=15, clarity_evidence=10
            if "skill_fit" in sb and isinstance(sb["skill_fit"], dict):
                sb["skill_fit"]["value"] = min(sb["skill_fit"].get("value", 0), 50)
            if "experience_fit" in sb and isinstance(sb["experience_fit"], dict):
                sb["experience_fit"]["value"] = min(sb["experience_fit"].get("value", 0), 25)
            if "ats_fit" in sb and isinstance(sb["ats_fit"], dict):
                sb["ats_fit"]["value"] = min(sb["ats_fit"].get("value", 0), 15)
            if "clarity_evidence" in sb and isinstance(sb["clarity_evidence"], dict):
                sb["clarity_evidence"]["value"] = min(sb["clarity_evidence"].get("value", 0), 10)
            
            # Recalculate total score to be safe
            total_score = 0
            total_score += sb.get("skill_fit", {}).get("value", 0)
            total_score += sb.get("experience_fit", {}).get("value", 0)
            total_score += sb.get("ats_fit", {}).get("value", 0)
            total_score += sb.get("clarity_evidence", {}).get("value", 0)
            analysis_json["score"] = total_score

        # Save to cache
        ai_result = await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=input_hash,
            output_json=analysis_json,
            provider=provider_name,
            model=model_name,
        )
        self.logger.info("Saved match analysis to cache: %s", input_hash[:16])

        return MatchAnalysisResult(
            analysis_id=ai_result.id,
            analysis=analysis_json,
            cache_hit=False,
        )
