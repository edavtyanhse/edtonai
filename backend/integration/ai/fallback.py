"""FallbackProvider — tries primary, silently switches to fallback on any error."""

from __future__ import annotations

import logging
from typing import Any

from backend.integration.ai.base import AIProvider

logger = logging.getLogger(__name__)


class FallbackProvider(AIProvider):
    """Tries primary provider; on failure falls back to secondary."""

    def __init__(self, primary: AIProvider, fallback: AIProvider) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = f"{primary.provider_name}→{fallback.provider_name}"

    @property
    def model_name(self) -> str:
        return getattr(self.primary, "model_name", None) or getattr(
            self.primary, "model", "unknown"
        )

    async def generate_json(
        self, prompt: str, prompt_name: str | None = None
    ) -> dict[str, Any]:
        try:
            return await self.primary.generate_json(prompt, prompt_name)
        except Exception as exc:
            logger.warning(
                "primary_provider_failed | provider=%s error=%s — switching to fallback",
                self.primary.provider_name,
                exc,
            )
            return await self.fallback.generate_json(prompt, prompt_name)
