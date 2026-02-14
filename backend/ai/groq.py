import json
import logging
from typing import Any

from groq import AsyncGroq

from backend.ai.base import AIProvider
from backend.ai.errors import AIError
from backend.core.config import settings

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """Groq AI provider implementation."""

    def __init__(self, model: str):
        if not settings.groq_api_key:
            raise ValueError("Groq API key is not configured")

        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = model
        self.provider_name = "groq"

    async def generate_json(self, prompt: str, prompt_name: str | None = None) -> dict[str, Any]:
        """Generate a JSON dictionary using Groq."""
        try:
            logger.info(f"Generating JSON with Groq model: {self.model}")

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that outputs JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                response_format={"type": "json_object"},
            )

            content = completion.choices[0].message.content
            if not content:
                raise AIError("Empty response from Groq")

            return json.loads(content)

        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise AIError(f"Groq generation failed: {e}") from e
