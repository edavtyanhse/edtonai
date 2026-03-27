import hashlib
import json
import logging
import time
from typing import Any

import httpx

from backend.core.config import settings
from backend.integration.ai.base import AIProvider
from backend.integration.ai.errors import AIRequestError, AIResponseFormatError
from backend.integration.ai.prompts import SYSTEM_PROMPT, VALIDATE_JSON_PROMPT


class DeepSeekProvider(AIProvider):
    """AI provider implementation for DeepSeek chat completions.

    All configuration is loaded from environment via settings.
    """

    def __init__(self) -> None:
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required (set in .env)")

        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.model = settings.ai_model
        self.timeout_seconds = settings.ai_timeout_seconds
        self.max_retries = settings.ai_max_retries
        self.temperature = settings.ai_temperature
        self.max_tokens = settings.ai_max_tokens
        self.provider_name = "deepseek"
        self.completions_url = f"{self.base_url}/chat/completions"
        self.logger = logging.getLogger(__name__)

    async def generate_json(
        self, prompt: str, prompt_name: str | None = None
    ) -> dict[str, Any]:
        prompt_name = prompt_name or "anonymous_prompt"
        input_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        try:
            raw_output, latency_ms = await self._call_model(prompt)
            parsed = await self._parse_or_validate(raw_output)
        except (AIRequestError, AIResponseFormatError) as exc:
            self.logger.error(
                "ai_call_failed | prompt_name=%s model=%s input_hash=%s error=%s",
                prompt_name,
                self.model,
                input_hash,
                str(exc),
                exc_info=exc,
            )
            raise

        self.logger.info(
            "ai_call_success | prompt_name=%s model=%s provider=%s input_hash=%s latency_ms=%d",
            prompt_name,
            self.model,
            self.provider_name,
            input_hash,
            latency_ms,
        )
        return parsed

    async def _call_model(self, user_prompt: str) -> tuple[str, int]:
        payload = {
            "model": self.model,
            "messages": self._build_messages(user_prompt),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,  # Enable streaming to avoid connection drops
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            start = time.monotonic()
            try:
                timeout = httpx.Timeout(
                    connect=30.0,  # Increased from 10s for slow networks
                    read=60.0,  # Timeout per chunk, not total
                    write=30.0,
                    pool=30.0,
                )
                async with httpx.AsyncClient(timeout=timeout) as client:
                    content = await self._stream_response(client, headers, payload)
                latency_ms = int((time.monotonic() - start) * 1000)
                return content, latency_ms
            except (
                httpx.TimeoutException,
                httpx.TransportError,
                httpx.HTTPStatusError,
                httpx.RemoteProtocolError,
            ) as exc:
                last_error = exc
                self.logger.warning(
                    "ai_request_retry | attempt=%d/%d error=%s",
                    attempt + 1,
                    self.max_retries + 1,
                    str(exc),
                )
                if attempt < self.max_retries:
                    continue
                raise AIRequestError(
                    f"DeepSeek request failed after retries: {exc}"
                ) from exc

        raise AIRequestError(f"DeepSeek request failed: {last_error}")

    async def _stream_response(
        self, client: httpx.AsyncClient, headers: dict, payload: dict
    ) -> str:
        """Stream response chunks to avoid connection timeout on long generations."""
        content_parts: list[str] = []

        async with client.stream(
            "POST", self.completions_url, headers=headers, json=payload
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            content_parts.append(delta["content"])
                    except json.JSONDecodeError:
                        continue  # Skip malformed chunks

        if not content_parts:
            raise AIResponseFormatError("Empty response from DeepSeek streaming")

        return "".join(content_parts)

    def _build_messages(self, user_prompt: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt},
        ]

    async def _parse_or_validate(self, raw_output: str) -> dict[str, Any]:
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            validated_text = await self._validate_with_model(raw_output)
            if validated_text is None:
                raise AIResponseFormatError(
                    "LLM output is not valid JSON and could not be recovered"
                )
            try:
                return json.loads(validated_text)
            except json.JSONDecodeError as exc:
                raise AIResponseFormatError(
                    "Validated LLM output is still not valid JSON"
                ) from exc

    async def _validate_with_model(self, raw_output: str) -> str | None:
        validation_prompt = VALIDATE_JSON_PROMPT.replace(
            "{{RAW_MODEL_OUTPUT}}", raw_output
        )
        try:
            validated_output, _ = await self._call_model(validation_prompt)
            return validated_output.strip() if validated_output else None
        except AIRequestError:
            return None
