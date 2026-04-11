"""HuggingFace Inference API provider (OpenAI-compatible endpoint)."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import httpx

from backend.integration.ai.base import AIProvider
from backend.integration.ai.errors import AIRequestError, AIResponseFormatError
from backend.integration.ai.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_BARE_RE = re.compile(r"\{.*\}", re.DOTALL)

HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"


def _extract_json(text: str) -> dict[str, Any]:
    """Try to extract JSON from model output that may have extra text around it."""
    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 2. Code block
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 3. Bare JSON anywhere in the text
    m = _JSON_BARE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise AIResponseFormatError(f"Cannot extract JSON from HF output: {text[:300]}")


class HuggingFaceProvider(AIProvider):
    """AI provider using HuggingFace Inference API (OpenAI-compatible).

    Works with any instruction-tuned model hosted on HF Hub.
    Uses the chat/completions endpoint with streaming.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        max_retries: int = 3,
        timeout_seconds: int = 120,
    ) -> None:
        self.model = model
        self.api_key = api_key or ""
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.provider_name = "huggingface"

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def generate_json(
        self, prompt: str, prompt_name: str | None = None
    ) -> dict[str, Any]:
        prompt_name = prompt_name or "anonymous"
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                start = time.monotonic()
                text = await self._call(prompt)
                latency = int((time.monotonic() - start) * 1000)
                result = _extract_json(text)
                logger.info(
                    "hf_call_ok | prompt=%s model=%s latency_ms=%d",
                    prompt_name, self.model, latency,
                )
                return result
            except AIResponseFormatError:
                raise  # Don't retry on format errors
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "hf_retry %d/%d | prompt=%s error=%s",
                    attempt + 1, self.max_retries, prompt_name, exc,
                )

        raise AIRequestError(
            f"HuggingFace request failed after {self.max_retries} attempts: {last_error}"
        )

    async def _call(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        timeout = httpx.Timeout(connect=30.0, read=self.timeout_seconds, write=30.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(HF_CHAT_URL, headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        if not content:
            raise AIResponseFormatError("Empty response from HuggingFace")
        return content
