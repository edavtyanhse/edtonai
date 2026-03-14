# AI Integration

Документация по интеграции с LLM-провайдерами.

## Содержание

- [Architecture](#architecture)
- [Hybrid AI Approach](#hybrid-ai-approach)
- [DeepSeek Provider](#deepseek-provider)
- [Groq Provider](#groq-provider)
- [Prompts](#prompts)
- [JSON Validation](#json-validation)
- [Error Handling](#error-handling)
- [Configuration](#configuration)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Services (CachedAIService)                     │
│  (ResumeService, VacancyService, MatchService, ...)            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ generate_json(prompt, prompt_name)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AIProvider (ABC)                            │
│                                                                 │
│  File: backend/integration/ai/base.py                          │
│                                                                 │
│  @abstractmethod                                                │
│  async def generate_json(prompt, prompt_name) -> dict           │
└────────────────┬────────────────────────────┬───────────────────┘
                 │ implements                  │ implements
                 ▼                             ▼
┌────────────────────────────┐ ┌──────────────────────────────────┐
│     DeepSeekProvider       │ │         GroqProvider             │
│                            │ │                                  │
│ File: integration/ai/      │ │ File: integration/ai/groq.py    │
│        deepseek.py         │ │                                  │
│                            │ │ • HTTP client (httpx)            │
│ • SSE streaming            │ │ • Sync JSON response             │
│ • Retry logic              │ │ • Retry logic                    │
│ • JSON validation fallback │ │ • Fast inference (Llama 3)       │
│ • Good for reasoning       │ │ • Good for parsing tasks         │
└────────────┬───────────────┘ └──────────────┬───────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────────┐ ┌──────────────────────────────────┐
│     DeepSeek API           │ │         Groq API                 │
│ api.deepseek.com/v1        │ │ api.groq.com/openai/v1           │
└────────────────────────────┘ └──────────────────────────────────┘
```

## Hybrid AI Approach

Проект использует **два AI-провайдера** для разных задач:

| Task Type | Provider | Model | Reason |
|-----------|----------|-------|--------|
| **Parsing** (resume, vacancy) | Groq | `llama-3.1-8b-instant` | Быстрый inference, достаточно для структурирования |
| **Reasoning** (match, adapt, ideal, cover letter) | DeepSeek | `deepseek-reasoner` | Глубокий анализ, сложные рассуждения |

Выбор провайдера определяется в `containers.py`:

```python
ai_provider_parsing = Factory(_create_ai_provider, settings=config, task_type="parsing")
ai_provider_reasoning = Factory(_create_ai_provider, settings=config, task_type="reasoning")

# ResumeService, VacancyService ← ai_provider_parsing (fast)
# MatchService, AdaptService, ... ← ai_provider_reasoning (smart)
```

Провайдер для каждого типа задачи настраивается через переменные окружения:
- `AI_PROVIDER_PARSING=groq` (default)
- `AI_PROVIDER_REASONING=deepseek` (default)

## DeepSeek Provider

### Файл

`backend/integration/ai/deepseek.py`

### Конфигурация

| Setting | Description | Default |
|---------|-------------|---------|
| `DEEPSEEK_API_KEY` | API ключ | required |
| `DEEPSEEK_BASE_URL` | Base URL | `https://api.deepseek.com/v1` |
| `AI_MODEL` | Модель | `deepseek-reasoner` |
| `AI_TIMEOUT_SECONDS` | Базовый таймаут | 180 |
| `AI_MAX_RETRIES` | Количество ретраев | 3 |
| `AI_TEMPERATURE` | Температура | 0.0 |
| `AI_MAX_TOKENS` | Max tokens | 4096 |

### Streaming (SSE)

DeepSeek API использует Server-Sent Events для потоковой передачи:
- При `stream: true` каждый токен отправляется сразу — соединение постоянно активно
- Предотвращает таймауты при долгой генерации

### Retry Logic

Ретраи на: `TimeoutException`, `TransportError`, `HTTPStatusError`, `RemoteProtocolError`.
НЕ ретраятся: невалидный JSON (используется validation fallback), auth ошибки.

## Groq Provider

### Файл

`backend/integration/ai/groq.py`

### Конфигурация

| Setting | Description | Default |
|---------|-------------|---------|
| `GROQ_API_KEY` | API ключ | required |
| `GROQ_MODEL_PARSING` | Модель для парсинга | `llama-3.1-8b-instant` |
| `GROQ_MODEL_REASONING` | Модель для рассуждений | `llama-3.3-70b-versatile` |

### Особенности

- Синхронный JSON-ответ (без streaming)
- Очень быстрый inference (~300ms)
- Используется для задач парсинга текста

## Prompts

### Файл

`backend/integration/ai/prompts.py`

### SYSTEM_PROMPT

Глобальный системный промпт для всех операций:

```
Ты — AI-модуль, встроенный в backend веб-сервиса.
Ты работаешь как часть программной системы, а не как чат.
Ты ОБЯЗАН возвращать ТОЛЬКО валидный JSON, без пояснений, без markdown.
```

### Операционные промпты

| Constant | Operation | Used by |
|----------|-----------|---------|
| `PARSE_RESUME_PROMPT` | parse_resume | ResumeService |
| `PARSE_VACANCY_PROMPT` | parse_vacancy | VacancyService |
| `ANALYZE_MATCH_PROMPT` | analyze_match | MatchService |
| `GENERATE_UPDATED_RESUME_PROMPT` | adapt_resume | AdaptResumeService |
| `IDEAL_RESUME_PROMPT` | ideal_resume | IdealResumeService |
| `COVER_LETTER_PROMPT` | generate_cover_letter | CoverLetterService |
| `VALIDATE_JSON_PROMPT` | (validation) | DeepSeekProvider |

## JSON Validation

### Проблема

LLM иногда возвращает невалидный JSON (комментарии, markdown-оформление, лишние запятые).

### Решение: Validation Fallback

1. Try `json.loads(raw_output)`
2. Fail → вызов LLM с `VALIDATE_JSON_PROMPT` для исправления
3. Fail → `AIResponseFormatError`

## Error Handling

### Exceptions

Определены в `backend/integration/ai/errors.py`:

| Exception | Cause | HTTP Code |
|-----------|-------|-----------|
| `AIError` | Базовый AI-ошибка | 502 |
| `AIRequestError` | Network/timeout/HTTP error | 502 |
| `AIResponseFormatError` | Invalid JSON after validation | 502 |

Также в `backend/errors/integration.py`:

| Exception | Cause | HTTP Code |
|-----------|-------|-----------|
| `AIProviderError` | Общая ошибка AI-провайдера | 502 |
| `ScraperError` | Ошибка web scraping | 502 / 422 |

Все ошибки обрабатываются **глобально** в `errors/handlers.py` — эндпоинты не содержат `try/except`.

## Configuration

### Environment Variables

```env
# DeepSeek (reasoning)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Groq (parsing)
GROQ_API_KEY=gsk_...
GROQ_MODEL_PARSING=llama-3.1-8b-instant
GROQ_MODEL_REASONING=llama-3.3-70b-versatile

# Provider selection
AI_PROVIDER_PARSING=groq       # groq | deepseek
AI_PROVIDER_REASONING=deepseek  # deepseek | groq

# General
AI_MODEL=deepseek-reasoner     # backward-compat model name
AI_TIMEOUT_SECONDS=180
AI_MAX_RETRIES=3
AI_TEMPERATURE=0.0
AI_MAX_TOKENS=4096
```

## Logging

Каждый вызов LLM логируется:

```
INFO | ai_call_success | prompt_name=parse_resume model=llama-3.1-8b-instant provider=groq input_hash=abc123... latency_ms=312
INFO | ai_call_success | prompt_name=analyze_match model=deepseek-reasoner provider=deepseek input_hash=def456... latency_ms=4521
WARNING | ai_request_retry | attempt=1/4 error=peer closed connection...
```
