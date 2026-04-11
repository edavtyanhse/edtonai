"""Local HuggingFace provider — loads model weights directly from HF Hub.

Suitable for development, demos, and environments without external API access.
Inference runs locally on CPU (or GPU if available).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend.integration.ai.base import AIProvider
from backend.integration.ai.errors import AIRequestError, AIResponseFormatError
from backend.integration.ai.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_JSON_BARE_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = _JSON_BARE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise AIResponseFormatError(f"Cannot extract JSON from model output: {text[:300]}")


class LocalHFProvider(AIProvider):
    """AI provider that loads model weights from HF Hub and runs inference locally.

    Model is loaded lazily on first call and cached in memory.
    Supports any causal LM from HuggingFace Hub.
    """

    def __init__(
        self,
        model_id: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> None:
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.provider_name = "local_hf"
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading local HF model: {self.model_id}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                dtype=torch.float32,
                device_map="auto" if torch.cuda.is_available() else "cpu",
            )
            logger.info(f"Local HF model loaded: {self.model_id}")
        except Exception as e:
            raise AIRequestError(f"Failed to load local HF model {self.model_id}: {e}") from e

    @property
    def model_name(self) -> str:
        return self.model_id

    async def generate_json(
        self, prompt: str, prompt_name: str | None = None
    ) -> dict[str, Any]:
        import asyncio

        self._load()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._generate_sync, prompt)
        return result

    def _generate_sync(self, prompt: str) -> dict[str, Any]:
        import torch

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": prompt},
        ]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        raw = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        logger.debug(f"LocalHF raw output: {raw[:200]}")
        return _extract_json(raw)
