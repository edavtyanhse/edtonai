# Backend Documentation

Техническая документация backend-сервиса адаптации резюме.

## 📚 Содержание

| Раздел | Описание |
|--------|----------|
| [API Specification](api/) | Спецификации REST API endpoints |
| [Architecture](architecture/) | Архитектура: FastAPI, Services, Repositories |
| [DB Schema](database/) | PostgreSQL, SQLAlchemy, RLS |
| [AI Integration](ai/) | DeepSeek LLM, промпты, валидация |
| [Configuration](configuration/) | Переменные окружения |

---

## 🛠️ Стек технологий

- **Language:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL 16 (Managed by **Supabase**)
- **ORM:** SQLAlchemy 2.0 (async) + AsyncPG
- **AI:** DeepSeek API
- **Auth:** JWT (Supabase Auth tokens)
- **Deployment:** Google Cloud Run

---

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- PostgreSQL (или Supabase проект)
- API Key от DeepSeek

### Локальный запуск

1. **Клонирование и venv:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Настройка окружения:**
   Создай `.env` (или используй системные переменные):
   ```env
   # Database (Supabase Transaction Pooler recommended)
   POSTGRES_USER=postgres.your-project
   POSTGRES_PASSWORD=your-db-password
   POSTGRES_HOST=aws-0-us-east-1.pooler.supabase.com
   POSTGRES_PORT=6543
   POSTGRES_DB=postgres

   # AI
   DEEPSEEK_API_KEY=sk-your-key
   AI_MODEL=deepseek-chat

   # Auth
   SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-settings
   ```

3. **Запуск:**
   ```bash
   python main.py
   # API будет доступно на http://localhost:8000
   # Swagger UI: http://localhost:8000/docs
   ```

---

## 🔐 Аутентификация и Безопасность

Сервис не занимается выпуском токенов (это делает Frontend через Supabase Auth).
Backend занимается **валидацией** JWT токенов.

1. **JWT Secret:** Переменная `SUPABASE_JWT_SECRET` используется для проверки подписи токена `Authorization: Bearer <token>`.
2. **User Identification:** Из токена извлекается `sub` (UUID пользователя), который используется для фильтрации данных (RLS на уровне приложения).
3. **RLS (Database):** На уровне базы данных также включены политики Row Level Security (хотя backend использует сервисный ключ или пользователя postgres, логика фильтрации дублируется в репозиториях для надежности, или используется пользователь с ограниченными правами). *Примечание: В текущей реализации мы фильтруем по `user_id` в репозиториях.*

---

## ☁️ Деплой (Google Cloud Run)

Сервис упаковывается в Docker контейнер и деплоится в Cloud Run.

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
# ... установка зависимостей ...
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Команда деплоя:**
```bash
gcloud run deploy edtonai-backend \
  --source . \
  --env-vars-file backend.env \
  --allow-unauthenticated
```
*Примечание: `--allow-unauthenticated` нужно, чтобы Frontend мог обращаться к API. Сами эндпоинты защищены проверкой JWT внутри приложения.*

---

## 🏗️ Структура проекта

```
backend/
├── main.py              # Entry point
├── core/
│   ├── auth.py          # JWT verification logic
│   ├── config.py        # Environment variables
├── api/v1/              # Endpoint controllers
├── services/            # Business logic (Resume, Vacancy, Match)
├── repositories/        # Database access
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas (DTO)
├── ai/                  # LLM integration (DeepSeek)
└── db/                  # Database session & base
```

## Переменные окружения (Полный список)

| Переменная | Описание |
|------------|----------|
| `DEEPSEEK_API_KEY` | Ключ API DeepSeek |
| `SUPABASE_JWT_SECRET` | Секрет для проверки JWT токенов (из Supabase Project Settings > API) |
| `POSTGRES_USER` | Пользователь БД |
| `POSTGRES_PASSWORD` | Пароль БД |
| `POSTGRES_HOST` | Хост БД |
| `POSTGRES_PORT` | Порт БД (обычно 5432 или 6543) |
| `POSTGRES_DB` | Имя БД |
