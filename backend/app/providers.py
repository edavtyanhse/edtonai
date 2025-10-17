# backend/app/providers.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os
import httpx


# ── .env загрузим гарантированно из backend/.env ──────────────────────────────
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class AIProvider:
    """
    Универсальный адаптер под OpenAI-совместимые чат-модели (DeepSeek/Qwen/OpenRouter).
    Ожидается, что AI_BASE_URL уже содержит нужную версию API (например, .../v1).
    Мы добавляем только путь ресурса: /chat/completions.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        timeout_s: float = 60.0,
    ) -> None:
        if not api_key:
            raise RuntimeError("AI_API_KEY пустой — проверь backend/.env")
        if not base_url:
            raise RuntimeError("AI_BASE_URL пустой — проверь backend/.env")

        # убираем завершающий слэш
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s

    async def chat(self, system: str, user: str) -> str:
        """
        Делает запрос к {base_url}/chat/completions и возвращает text контента.
        Если провайдер отвечает ошибкой — кидает RuntimeError с телом ответа.
        """
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                # пробрасываем тело ответа — помогает быстро понять, что не так (ключ/модель/лимиты)
                raise RuntimeError(f"AI HTTP {resp.status_code} at {url}: {resp.text}")

            data = resp.json()
            # ожидаем OpenAI-подобный формат
            try:
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                raise RuntimeError(f"Unexpected AI response schema: {data}") from e


_provider: Optional[AIProvider] = None


def get_ai() -> AIProvider:
    """
    Ленивый синглтон провайдера — читает конфиг из .env один раз.
    """
    global _provider
    if _provider is not None:
        return _provider

    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
    api_key = os.getenv("AI_API_KEY", "")
    model = os.getenv("AI_MODEL", "deepseek-chat")
    temperature = float(os.getenv("TEMPERATURE", "0.3"))
    max_tokens = int(os.getenv("MAX_TOKENS", "1500"))

    _provider = AIProvider(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return _provider
