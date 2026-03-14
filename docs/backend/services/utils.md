# Утилиты сервисного слоя

Модуль вспомогательных функций для нормализации текста, хеширования и работы с AI-провайдерами.

## Файл

`backend/services/utils.py`

## Функции

### `normalize_text(text: str) -> str`

Нормализация текста для стабильного хеширования:
- Trim whitespace
- Замена табов на пробелы
- Collapse множественных пробелов → один пробел
- Collapse множественных пустых строк → одна
- Trim каждой строки

### `compute_hash(text: str) -> str`

SHA256-хеш нормализованного текста. Используется для определения дубликатов резюме / вакансий.

### `prompt_template_sha256(prompt_template: str) -> str`

SHA256-хеш prompt-шаблона. Включается в cache key, чтобы при изменении промпта кеш инвалидировался.

### `get_provider_name(provider: Any) -> str`

Извлекает `provider_name` из AI-провайдера (для логирования и cache key).

### `get_model_name(provider: Any, fallback: str = "unknown") -> str`

Извлекает `model` или `model_name` из AI-провайдера.

### `compute_ai_cache_key(operation: str, payload: dict) -> str`

Стабильный cache key для `AIResult`, строится как:

```python
data = {"operation": operation, **payload}
dumped = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
return hashlib.sha256(dumped.encode("utf-8")).hexdigest()
```

Вызывающий код отвечает за передачу хешированных входных данных (а не сырого текста) для уменьшения размера ключа.

## Использование

Все AI-сервисы (через `CachedAIService`) используют эти утилиты для:
- Вычисления хеша входного текста (`compute_hash`)
- Включения prompt hash в cache key (`prompt_template_sha256`)
- Получения provider/model для cache key (`get_provider_name`, `get_model_name`)
- Формирования финального cache key (`compute_ai_cache_key`)
