"""Base class for AI-powered services with result caching.

Eliminates duplicated cache-check / cache-save / provider-info boilerplate
across ResumeService, VacancyService, MatchService, AdaptResumeService,
CoverLetterService and IdealResumeService.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.integration.ai.base import AIProvider
from backend.repositories.interfaces import IAIResultRepository
from backend.services.utils import get_model_name, get_provider_name


class CachedAIService:
    """Base class for services that call an AI provider and cache results.

    Provides
    --------
    * Common attributes: ``session``, ``ai_provider``, ``settings``, ``logger``.
    * ``provider_name`` / ``model_name`` — resolved from the AI provider instance.
    * ``_check_cache`` / ``_save_to_cache`` — thin wrappers around
      :pyclass:`IAIResultRepository`.
    * ``_call_ai_with_cache`` — full cache-through shortcut (check → call → save).

    Subclasses **must** define the ``OPERATION`` class-level attribute.

    ``ai_result_repo`` is optional: services that use a different caching
    strategy (e.g. ``IdealResumeService``) may pass ``None``.
    """

    OPERATION: str  # e.g. "parse_resume", "analyze_match", …

    def __init__(
        self,
        session: AsyncSession,
        ai_provider: AIProvider,
        settings: Settings,
        ai_result_repo: IAIResultRepository | None = None,
    ) -> None:
        self.session = session
        self.ai_provider = ai_provider
        self.settings = settings
        self.ai_result_repo = ai_result_repo
        self.logger = logging.getLogger(type(self).__module__)

    # ── Provider info helpers ─────────────────────────────────────

    @property
    def provider_name(self) -> str:
        """Current AI provider name (e.g. ``'groq'``, ``'deepseek'``)."""
        return get_provider_name(self.ai_provider)

    @property
    def model_name(self) -> str:
        """Current AI model name, with Settings fallback."""
        return get_model_name(self.ai_provider, fallback=self.settings.ai_model)

    # ── AIResult-based caching ────────────────────────────────────

    async def _check_cache(self, input_hash: str) -> Any | None:
        """Look up an ``AIResult`` by ``(OPERATION, input_hash)``.

        Returns the ORM object or ``None`` when not found (or when
        ``ai_result_repo`` is not configured).
        """
        if self.ai_result_repo is None:
            return None
        return await self.ai_result_repo.get(self.OPERATION, input_hash)

    async def _save_to_cache(
        self,
        input_hash: str,
        output_json: dict[str, Any],
    ) -> Any:
        """Persist an AI result into the cache table.

        Returns the created ``AIResult`` ORM object.

        Raises
        ------
        RuntimeError
            If ``ai_result_repo`` was not provided.
        """
        if self.ai_result_repo is None:
            raise RuntimeError("Cannot save to cache: ai_result_repo is not configured")
        return await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=input_hash,
            output_json=output_json,
            provider=self.provider_name,
            model=self.model_name,
        )

    async def _call_ai_with_cache(
        self,
        input_hash: str,
        prompt: str,
    ) -> tuple[dict[str, Any], bool]:
        """Full cache-through AI call.

        1. Check cache by ``(OPERATION, input_hash)``
        2. On hit → return ``(output_json, True)``
        3. Call ``ai_provider.generate_json``
        4. Post-process output via ``_post_process_output`` (hook)
        5. Save to cache
        6. Return ``(output_json, False)``
        """
        cached = await self._check_cache(input_hash)
        if cached is not None:
            self.logger.info(
                "Cache hit for %s: %s",
                self.OPERATION,
                input_hash[:16],
            )
            return cached.output_json, True

        output_json = await self.ai_provider.generate_json(
            prompt,
            prompt_name=self.OPERATION,
        )

        output_json = self._post_process_output(output_json)

        await self._save_to_cache(input_hash, output_json)
        self.logger.info(
            "Saved %s to cache: %s",
            self.OPERATION,
            input_hash[:16],
        )

        return output_json, False

    # ── Hooks ─────────────────────────────────────────────────────

    def _post_process_output(self, output_json: dict[str, Any]) -> dict[str, Any]:
        """Transform AI output before it is saved to cache.

        Override in subclasses that need post-processing (e.g. score clamping
        in ``MatchService``).  The default implementation is a no-op.
        """
        return output_json
