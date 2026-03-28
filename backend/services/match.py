"""Match service - analyze resume-vacancy match and cache result."""

import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.domain.match import MatchAnalysisResult
from backend.integration.ai.base import AIProvider
from backend.integration.ai.prompts import (
    ANALYZE_MATCH_PROMPT,
    ANALYZE_MATCH_WITH_CONTEXT_PROMPT,
)
from backend.repositories.interfaces import IAIResultRepository
from backend.services.base import CachedAIService
from backend.services.utils import (
    compute_ai_cache_key,
    prompt_template_sha256,
)

# Score clamping limits per breakdown category
_SCORE_LIMITS: dict[str, int] = {
    "skill_fit": 50,
    "experience_fit": 25,
    "ats_fit": 15,
    "clarity_evidence": 10,
}


class MatchService(CachedAIService):
    """Service for analyzing resume-vacancy match."""

    OPERATION = "analyze_match"

    def __init__(
        self,
        session: AsyncSession,
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

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _compute_match_hash(
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
    ) -> str:
        """Compute hash from parsed resume and vacancy JSONs."""
        combined = json.dumps(parsed_resume, sort_keys=True) + json.dumps(
            parsed_vacancy, sort_keys=True
        )
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @staticmethod
    def _clamp_scores(analysis: dict[str, Any]) -> dict[str, Any]:
        """Recalculate formula-based scores from actual data, then clamp to limits."""
        if "score_breakdown" not in analysis:
            return analysis

        sb = analysis["score_breakdown"]

        # Recalculate ats_fit from actual coverage ratio (formula: ratio * 15)
        ats = analysis.get("ats", {})
        coverage = ats.get("coverage_ratio")
        if coverage is not None and isinstance(sb.get("ats_fit"), dict):
            sb["ats_fit"]["value"] = round(coverage * 15)

        # Recalculate skill_fit from actual matched/missing lists
        # Formula: (matched_required / total_required) * 40 + (matched_preferred / total_preferred) * 10
        matched_req = len(analysis.get("matched_required_skills", []))
        missing_req = len(analysis.get("missing_required_skills", []))
        total_req = matched_req + missing_req
        matched_pref = len(analysis.get("matched_preferred_skills", []))
        missing_pref = len(analysis.get("missing_preferred_skills", []))
        total_pref = matched_pref + missing_pref

        if total_req > 0 and isinstance(sb.get("skill_fit"), dict):
            req_score = round((matched_req / total_req) * 40)
            pref_score = round((matched_pref / total_pref) * 10) if total_pref > 0 else 10
            sb["skill_fit"]["value"] = req_score + pref_score

        # Clamp to limits
        for category, limit in _SCORE_LIMITS.items():
            entry = sb.get(category)
            if isinstance(entry, dict) and "value" in entry:
                entry["value"] = min(entry["value"], limit)

        analysis["score"] = sum(
            sb.get(cat, {}).get("value", 0) for cat in _SCORE_LIMITS
        )
        return analysis

    @staticmethod
    def _ensure_gaps_for_missing_skills(analysis: dict[str, Any]) -> dict[str, Any]:
        """Ensure every missing_required_skill has a corresponding gap and checkbox."""
        gaps = analysis.get("gaps", [])
        checkboxes = analysis.get("checkbox_options", [])
        existing_gap_ids = {g["id"] for g in gaps}

        missing_required = analysis.get("missing_required_skills", [])
        missing_preferred = analysis.get("missing_preferred_skills", [])

        # Check which missing skills already have a gap (by checking message content)
        gap_texts = " ".join(g.get("message", "") for g in gaps).lower()

        next_id = len(gaps) + 1
        for skill in missing_required:
            if skill.lower() not in gap_texts:
                gap_id = f"gap-{next_id:03d}"
                while gap_id in existing_gap_ids:
                    next_id += 1
                    gap_id = f"gap-{next_id:03d}"
                gaps.append({
                    "id": gap_id,
                    "type": "missing_skill",
                    "severity": "high",
                    "message": f"Отсутствует: {skill}",
                    "suggestion": f"Добавить {skill}",
                    "target_section": "skills",
                })
                checkboxes.append({
                    "id": gap_id,
                    "label": f"Добавить {skill}",
                    "description": f"Добавить {skill} в резюме",
                    "category": "skills",
                    "impact": "high",
                    "requires_user_input": True,
                    "user_input_placeholder": f"Опишите ваш опыт: {skill}",
                })
                existing_gap_ids.add(gap_id)
                next_id += 1

        for skill in missing_preferred:
            if skill.lower() not in gap_texts:
                gap_id = f"gap-{next_id:03d}"
                while gap_id in existing_gap_ids:
                    next_id += 1
                    gap_id = f"gap-{next_id:03d}"
                gaps.append({
                    "id": gap_id,
                    "type": "missing_skill",
                    "severity": "medium",
                    "message": f"Отсутствует (желательно): {skill}",
                    "suggestion": f"Добавить {skill}",
                    "target_section": "skills",
                })
                checkboxes.append({
                    "id": gap_id,
                    "label": f"Добавить {skill}",
                    "description": f"Добавить {skill} в резюме",
                    "category": "skills",
                    "impact": "medium",
                    "requires_user_input": True,
                    "user_input_placeholder": f"Опишите ваш опыт: {skill}",
                })
                existing_gap_ids.add(gap_id)
                next_id += 1

        analysis["gaps"] = gaps
        analysis["checkbox_options"] = checkboxes
        return analysis

    @staticmethod
    def _filter_new_gaps(
        analysis: dict[str, Any], original_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Remove gaps from re-analysis that weren't in the original analysis."""
        original_gap_ids = {g["id"] for g in original_analysis.get("gaps", [])}
        analysis["gaps"] = [
            g for g in analysis.get("gaps", []) if g["id"] in original_gap_ids
        ]
        analysis["checkbox_options"] = [
            c for c in analysis.get("checkbox_options", [])
            if c["id"] in original_gap_ids
        ]
        return analysis

    def _post_process_output(self, output_json: dict[str, Any]) -> dict[str, Any]:
        """Clamp scores and ensure gaps consistency."""
        output_json = self._clamp_scores(output_json)
        output_json = self._ensure_gaps_for_missing_skills(output_json)
        return output_json

    # ── Public API ────────────────────────────────────────────────

    async def analyze_and_cache(
        self,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
    ) -> MatchAnalysisResult:
        """Analyze match and cache result.

        1. Compute hash from both parsed JSONs
        2. Check AIResult cache (via base class)
        3. If not cached, call LLM, clamp scores, save result
        """
        base_hash = self._compute_match_hash(parsed_resume, parsed_vacancy)
        prompt_sha = prompt_template_sha256(ANALYZE_MATCH_PROMPT)
        input_hash = compute_ai_cache_key(
            self.OPERATION,
            {
                "base_hash": base_hash,
                "provider": self.provider_name,
                "model": self.model_name,
                "prompt_sha256": prompt_sha,
                "temperature": self.settings.ai_temperature,
                "max_tokens": self.settings.ai_max_tokens,
            },
        )

        # Check cache
        cached = await self._check_cache(input_hash)
        if cached is not None:
            return MatchAnalysisResult(
                analysis_id=cached.id,
                analysis=cached.output_json,
                cache_hit=True,
            )

        # Build prompt & call LLM
        prompt = ANALYZE_MATCH_PROMPT.replace(
            "{{PARSED_RESUME_JSON}}",
            json.dumps(parsed_resume, ensure_ascii=False, indent=2),
        ).replace(
            "{{PARSED_VACANCY_JSON}}",
            json.dumps(parsed_vacancy, ensure_ascii=False, indent=2),
        )

        analysis_json = await self.ai_provider.generate_json(
            prompt,
            prompt_name=self.OPERATION,
        )
        analysis_json = self._clamp_scores(analysis_json)
        analysis_json = self._ensure_gaps_for_missing_skills(analysis_json)

        # Save to cache
        ai_result = await self._save_to_cache(input_hash, analysis_json)

        return MatchAnalysisResult(
            analysis_id=ai_result.id,
            analysis=analysis_json,
            cache_hit=False,
        )

    async def analyze_with_context(
        self,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
        original_analysis: dict[str, Any],
        applied_checkbox_ids: list[str],
    ) -> MatchAnalysisResult:
        """Re-analyze match with awareness of applied improvements.

        Uses a context-aware prompt that:
        - Knows which improvements were applied
        - Moves applied skills from missing to matched
        - Recalculates score upward
        - Removes addressed gaps
        """
        # Build applied_improvements detail from original analysis gaps
        applied_details = []
        gaps_by_id = {g["id"]: g for g in original_analysis.get("gaps", [])}
        for cid in applied_checkbox_ids:
            gap = gaps_by_id.get(cid)
            if gap:
                applied_details.append(
                    {
                        "checkbox_id": cid,
                        "type": gap.get("type", "unknown"),
                        "message": gap.get("message", ""),
                        "target_section": gap.get("target_section", "other"),
                    }
                )

        # Cache key includes applied improvements
        base_hash = self._compute_match_hash(parsed_resume, parsed_vacancy)
        applied_hash = hashlib.sha256(
            json.dumps(sorted(applied_checkbox_ids)).encode("utf-8")
        ).hexdigest()
        prompt_sha = prompt_template_sha256(ANALYZE_MATCH_WITH_CONTEXT_PROMPT)
        input_hash = compute_ai_cache_key(
            "analyze_match_with_context",
            {
                "base_hash": base_hash,
                "applied_hash": applied_hash,
                "provider": self.provider_name,
                "model": self.model_name,
                "prompt_sha256": prompt_sha,
                "temperature": self.settings.ai_temperature,
                "max_tokens": self.settings.ai_max_tokens,
            },
        )

        # Check cache
        cached = await self._check_cache(input_hash)
        if cached is not None:
            return MatchAnalysisResult(
                analysis_id=cached.id,
                analysis=cached.output_json,
                cache_hit=True,
            )

        # Build prompt
        prompt = (
            ANALYZE_MATCH_WITH_CONTEXT_PROMPT.replace(
                "{{PARSED_RESUME_JSON}}",
                json.dumps(parsed_resume, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{PARSED_VACANCY_JSON}}",
                json.dumps(parsed_vacancy, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{ORIGINAL_ANALYSIS_JSON}}",
                json.dumps(original_analysis, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{APPLIED_IMPROVEMENTS_JSON}}",
                json.dumps(applied_details, ensure_ascii=False, indent=2),
            )
        )

        analysis_json = await self.ai_provider.generate_json(
            prompt,
            prompt_name="analyze_match_with_context",
        )
        analysis_json = self._clamp_scores(analysis_json)

        # Remove gaps that weren't in the original analysis (no surprise new gaps)
        analysis_json = self._filter_new_gaps(analysis_json, original_analysis)

        # Ensure score never decreases after improvements
        original_score = original_analysis.get("score", 0)
        if analysis_json.get("score", 0) < original_score:
            analysis_json["score"] = original_score
            # Also floor each breakdown category to its original value
            orig_sb = original_analysis.get("score_breakdown", {})
            new_sb = analysis_json.get("score_breakdown", {})
            for cat in _SCORE_LIMITS:
                orig_val = orig_sb.get(cat, {}).get("value", 0)
                new_val = new_sb.get(cat, {}).get("value", 0)
                if new_val < orig_val and cat in new_sb:
                    new_sb[cat]["value"] = orig_val
            # Recalculate total after floor
            analysis_json["score"] = sum(
                new_sb.get(cat, {}).get("value", 0) for cat in _SCORE_LIMITS
            )

        # Save to cache
        ai_result = await self._save_to_cache(input_hash, analysis_json)

        return MatchAnalysisResult(
            analysis_id=ai_result.id,
            analysis=analysis_json,
            cache_hit=False,
        )
