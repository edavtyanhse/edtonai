"""Match service - analyze resume-vacancy match and cache result."""

import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.domain.match import MatchAnalysisResult
from backend.integration.ai.base import AIProvider
from backend.integration.ai.scorer import ResumeScorer
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
        scorer: ResumeScorer | None = None,
    ) -> None:
        super().__init__(
            session=session,
            ai_provider=ai_provider,
            settings=settings,
            ai_result_repo=ai_result_repo,
        )
        self._scorer = scorer

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
            pref_score = (
                round((matched_pref / total_pref) * 10) if total_pref > 0 else 10
            )
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
                gaps.append(
                    {
                        "id": gap_id,
                        "type": "missing_skill",
                        "severity": "high",
                        "message": f"Отсутствует: {skill}",
                        "suggestion": f"Добавить {skill}",
                        "target_section": "skills",
                    }
                )
                checkboxes.append(
                    {
                        "id": gap_id,
                        "label": f"Добавить {skill}",
                        "description": f"Добавить {skill} в резюме",
                        "category": "skills",
                        "impact": "high",
                        "requires_user_input": True,
                        "user_input_placeholder": f"Опишите ваш опыт: {skill}",
                    }
                )
                existing_gap_ids.add(gap_id)
                next_id += 1

        for skill in missing_preferred:
            if skill.lower() not in gap_texts:
                gap_id = f"gap-{next_id:03d}"
                while gap_id in existing_gap_ids:
                    next_id += 1
                    gap_id = f"gap-{next_id:03d}"
                gaps.append(
                    {
                        "id": gap_id,
                        "type": "missing_skill",
                        "severity": "medium",
                        "message": f"Отсутствует (желательно): {skill}",
                        "suggestion": f"Добавить {skill}",
                        "target_section": "skills",
                    }
                )
                checkboxes.append(
                    {
                        "id": gap_id,
                        "label": f"Добавить {skill}",
                        "description": f"Добавить {skill} в резюме",
                        "category": "skills",
                        "impact": "medium",
                        "requires_user_input": True,
                        "user_input_placeholder": f"Опишите ваш опыт: {skill}",
                    }
                )
                existing_gap_ids.add(gap_id)
                next_id += 1

        analysis["gaps"] = gaps
        analysis["checkbox_options"] = checkboxes
        return analysis

    @staticmethod
    def _filter_new_gaps(
        analysis: dict[str, Any],
        original_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Remove gaps from re-analysis that weren't in the original analysis.

        Also reconciles missing/matched skill lists so that skills which were
        matched in the original analysis can't reappear as missing after re-analysis
        (LLM sometimes re-evaluates the adapted resume and "forgets" previously
        matched skills).
        """
        original_gap_ids = {g["id"] for g in original_analysis.get("gaps", [])}
        analysis["gaps"] = [
            g for g in analysis.get("gaps", []) if g["id"] in original_gap_ids
        ]
        analysis["checkbox_options"] = [
            c
            for c in analysis.get("checkbox_options", [])
            if c["id"] in original_gap_ids
        ]

        # Skills that were matched in original must stay matched.
        # Remove them from missing_* lists and add to matched_* if absent.
        orig_matched_req = set(original_analysis.get("matched_required_skills", []))
        orig_matched_pref = set(original_analysis.get("matched_preferred_skills", []))

        new_missing_req = analysis.get("missing_required_skills", [])
        new_missing_pref = analysis.get("missing_preferred_skills", [])
        new_matched_req = analysis.get("matched_required_skills", [])
        new_matched_pref = analysis.get("matched_preferred_skills", [])

        # Required skills
        wrongly_missing_req = [s for s in new_missing_req if s in orig_matched_req]
        if wrongly_missing_req:
            analysis["missing_required_skills"] = [
                s for s in new_missing_req if s not in orig_matched_req
            ]
            existing_matched_req = set(new_matched_req)
            analysis["matched_required_skills"] = new_matched_req + [
                s for s in wrongly_missing_req if s not in existing_matched_req
            ]

        # Preferred skills
        wrongly_missing_pref = [s for s in new_missing_pref if s in orig_matched_pref]
        if wrongly_missing_pref:
            analysis["missing_preferred_skills"] = [
                s for s in new_missing_pref if s not in orig_matched_pref
            ]
            existing_matched_pref = set(new_matched_pref)
            analysis["matched_preferred_skills"] = new_matched_pref + [
                s for s in wrongly_missing_pref if s not in existing_matched_pref
            ]

        return analysis

    @staticmethod
    def _force_apply_skill_moves(
        analysis: dict[str, Any],
        applied_details: list[dict[str, Any]],
        orig_missing_req: list[str] | None = None,
        orig_missing_pref: list[str] | None = None,
    ) -> dict[str, Any]:
        """Deterministically move applied skills from missing→matched.

        Two mechanisms combined:
        1. Standard: gaps with prefix "Отсутствует: skill" → exact skill name.
        2. Broad: ANY applied gap → scan all original missing skill names for
           substring match against the gap message.  Handles LLM-generated gaps
           with non-standard messages (e.g. combined list) and experience_gap /
           weak_wording gaps that mention skills in their description.

        The broad mechanism requires orig_missing_req / orig_missing_pref to be
        passed from the caller so we know the full original missing skill lists.
        """
        # Build lowercase index of all applied gap messages
        applied_messages_lower = [
            d.get("message", "").lower() for d in applied_details
        ]

        def _skill_is_addressed(skill: str) -> bool:
            """Return True if this skill is mentioned in any applied gap message."""
            return any(skill.lower() in msg for msg in applied_messages_lower)

        def _move(
            missing_key: str,
            matched_key: str,
            orig_missing: list[str] | None,
        ) -> None:
            missing = list(analysis.get(missing_key, []))
            matched = list(analysis.get(matched_key, []))

            to_move: list[str] = []
            # Mechanism 1+2: check current missing list
            for skill in missing:
                if _skill_is_addressed(skill):
                    to_move.append(skill)

            # Mechanism 2 (extended): also check original missing list in case
            # LLM re-named a skill slightly in the new analysis output
            if orig_missing:
                already_moving = {s.lower() for s in to_move}
                already_missing = {s.lower() for s in missing}
                for orig_skill in orig_missing:
                    ol = orig_skill.lower()
                    if (
                        ol not in already_moving
                        and ol in already_missing
                        and _skill_is_addressed(orig_skill)
                    ):
                        # find the actual skill in missing (case may differ)
                        for s in missing:
                            if s.lower() == ol:
                                to_move.append(s)
                                break

            if to_move:
                to_move_lower = {s.lower() for s in to_move}
                analysis[missing_key] = [
                    s for s in missing if s.lower() not in to_move_lower
                ]
                existing = {s.lower() for s in matched}
                analysis[matched_key] = matched + [
                    s for s in to_move if s.lower() not in existing
                ]

        _move("missing_required_skills", "matched_required_skills", orig_missing_req)
        _move("missing_preferred_skills", "matched_preferred_skills", orig_missing_pref)

        # Also update ATS keywords: move any keyword mentioned in applied gap messages
        ats = analysis.get("ats", {})
        missing_kw = ats.get("missing_keywords", [])
        covered_kw = ats.get("covered_keywords", [])
        kw_to_move = [k for k in missing_kw if _skill_is_addressed(k)]
        if kw_to_move:
            kw_lower = {k.lower() for k in kw_to_move}
            ats["missing_keywords"] = [
                k for k in missing_kw if k.lower() not in kw_lower
            ]
            existing_kw = {k.lower() for k in covered_kw}
            ats["covered_keywords"] = covered_kw + [
                k for k in kw_to_move if k.lower() not in existing_kw
            ]
            total_kw = len(ats["covered_keywords"]) + len(ats["missing_keywords"])
            if total_kw > 0:
                ats["coverage_ratio"] = round(
                    len(ats["covered_keywords"]) / total_kw, 2
                )
            analysis["ats"] = ats

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

        # Semantic score hint from cross-encoder
        score_hint = ""
        if self._scorer is not None:
            resume_str = json.dumps(parsed_resume, ensure_ascii=False)
            vacancy_str = json.dumps(parsed_vacancy, ensure_ascii=False)
            semantic_score = self._scorer.score(resume_str, vacancy_str)
            if semantic_score is not None:
                score_hint = (
                    f"Подсказка: семантическая совместимость резюме и вакансии "
                    f"по оценке cross-encoder модели = {semantic_score}/100. "
                    f"Используй как ориентир при выставлении итогового score.\n\n"
                )

        # Build prompt & call LLM
        prompt = ANALYZE_MATCH_PROMPT.replace(
            "{{SEMANTIC_SCORE_HINT}}",
            score_hint,
        ).replace(
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
                "pp_version": "4",  # increment when post-processing logic changes
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

        # Step 1: Deterministically move applied missing skills from missing→matched.
        # Pass original missing lists so broad substring matching can catch skills
        # referenced in combined/non-standard gap messages.
        analysis_json = self._force_apply_skill_moves(
            analysis_json,
            applied_details,
            orig_missing_req=original_analysis.get("missing_required_skills"),
            orig_missing_pref=original_analysis.get("missing_preferred_skills"),
        )

        # Step 2: Reconcile skills that were matched in original (LLM must not
        # "forget" them) and remove any unexpected new gaps it hallucinated.
        # Must happen BEFORE _clamp_scores so the score reflects all reconciled lists.
        analysis_json = self._filter_new_gaps(analysis_json, original_analysis)

        # Step 3: Remove gaps that the user already addressed.
        applied_ids_set = set(applied_checkbox_ids)
        analysis_json["gaps"] = [
            g for g in analysis_json.get("gaps", [])
            if g["id"] not in applied_ids_set
        ]
        analysis_json["checkbox_options"] = [
            c for c in analysis_json.get("checkbox_options", [])
            if c["id"] not in applied_ids_set
        ]

        # Step 4: Recalculate scores from the fully reconciled skill lists.
        analysis_json = self._clamp_scores(analysis_json)

        # Step 5: Floor individual score categories to their original values.
        # Applied improvements can only raise scores, never lower them.
        orig_sb = original_analysis.get("score_breakdown", {})
        new_sb = analysis_json.get("score_breakdown", {})
        for cat in _SCORE_LIMITS:
            orig_val = orig_sb.get(cat, {}).get("value", 0)
            new_val = new_sb.get(cat, {}).get("value", 0)
            if new_val < orig_val and cat in new_sb:
                new_sb[cat]["value"] = orig_val
        # Recalculate total after flooring
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
