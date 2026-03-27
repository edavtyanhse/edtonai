# EdTon.ai — AI Resume Adapter Service 🚀

**EdtonAI** — это веб-сервис для умной адаптации резюме под конкретные вакансии с использованием искусственного интеллекта. Проект помогает кандидатам повысить шансы на прохождение ATS (Applicant Tracking Systems) и рекрутерского скрининга, генерируя оптимизированные версии резюме и сопроводительные письма.

## ✨ Основные возможности

*   **Умный парсинг**: Извлечение данных из резюме (PDF/DOCX/TXT) и вакансий (URL/Text) с помощью AI (Groq/Llama 3.1).
*   **Gap Analysis**: Детальный анализ соответствия резюме требованиям вакансии с выявлением недостающих навыков и ключевых слов (Groq/Llama 3.3 70B Versatile).
*   **AI Адаптация**: Автоматическое переписывание summary и bullet points опыта работы для закрытия найденных гэпов.
*   **Генерация Cover Letter**: Создание персонализированных сопроводительных писем под вакансию.
*   **История версий**: Полный контроль над версиями резюме, возможность отката и сравнения.
*   **Wizard (автосохранение)**: Состояние визарда автоматически сохраняется в localStorage (можно обновить страницу и продолжить с того же места).

---

## 📚 Документация (Artifacts)

Для защиты и изучения проекта подготовлены следующие документы:

*   **[Архитектура (C4 Model)](docs/ARCHITECTURE.md)**: Диаграммы Context, Container, Deployment.
*   **[User Story Map](docs/USER_STORY_MAP.md)**: Планы MVP/MUP, сценарии использования.
*   **[Материалы для презентации](docs/MVP_PRESENTATION_CONTENT.md)**: Структура и контент для слайдов защиты.

---

## 🏗️ Архитектура

Подробная документация архитектуры (C4 Model, Deployment) доступна здесь: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Общая схема (System Context)

```mermaid
graph LR
    User[Job Seeker] -- HTTPS --> Web[EdTon.ai Web App]
    Web -- JSON/HTTPS --> API[Backend API]
    API -- SQL --> DB[(Supabase / PostgreSQL)]
    API -- REST --> AI1[Groq (Reasoning: Llama 3.3 70B Versatile)]
    API -- REST --> AI2[Groq (Parsing: Llama 3.1 8B Instant)]
```

### 📂 Структура репозитория

```
edtonai/
├── backend/                # FastAPI приложение
│   ├── ai/                 # Логика работы с LLM (DeepSeek, Groq)
│   ├── core/               # Конфигурация, БД, логирование
│   ├── services/           # Бизнес-логика (Resume, Vacancy, Match)
│   └── main.py             # Точка входа
├── frontend/               # React (Vite) приложение
│   ├── src/
│   │   ├── api/            # Типы и клиенты API
│   │   ├── components/     # UI компоненты
│   │   ├── pages/          # Страницы приложения (Wizard, History)
│   │   └── hooks/          # React hooks
├── cloudbuild.yaml         # Google Cloud Build пайплайн
├── docker-compose.yml      # Локальный запуск
└── README.md               # Этот файл
```

---

## 🛠️ Технологический стек

### Backend
*   **Язык**: Python 3.11+
*   **Фреймворк**: FastAPI
*   **БД**: PostgreSQL 15+ (via Supabase)
*   **ORM**: SQLAlchemy 2.0 (Async)
*   **AI**: DeepSeek V3, Groq (Llama 3.1, Llama 3.3)
*   **Инфра**: Docker, Google Cloud Run

### Frontend
*   **Язык**: TypeScript
*   **Фреймворк**: React 18, Vite
*   **State**: TanStack Query (React Query)
*   **UI**: Tailwind CSS, Lucide Icons
*   **Auth**: Supabase Auth

---

## 🚀 Инструкция по запуску

### Предварительные требования
*   **Docker & Docker Compose** (рекомендуемый способ).
*   **Supabase Account**: нужен URL и API ключи.
*   **API Keys**: DeepSeek API Key, Groq API Key.

### Шаг 1: Клонирование
```bash
git clone https://github.com/edavtyanhse/edtonai.git
cd edtonai
```

### Шаг 2: Настройка окружения
Создайте файл `.env` в корне проекта на основе примера.
**Обязательные переменные:**

```ini
# Database
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.supabase.co:5432/postgres

# Auth (Supabase)
VITE_SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
VITE_SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_JWT_SECRET=[YOUR-JWT-SECRET]

# AI Providers
DEEPSEEK_API_KEY=[YOUR-KEY]
GROQ_API_KEY=[YOUR-KEY]

# Config
AI_PROVIDER_PARSING=groq
AI_PROVIDER_REASONING=groq
```

### Шаг 3: Запуск (Docker Compose)
Запустите полный стек (фронтенд + бэкенд) одной командой:

```bash
docker-compose up -d --build
```

После запуска приложение доступно по адресам:
*   **Frontend**: http://localhost:3000
*   **Backend Swagger**: http://localhost:8000/docs

### 🧪 Запуск тестов (Backend)
```bash
cd backend
pytest
```

---

## ☁️ Деплой (Google Cloud)

Проект настроен на CI/CD через **Google Cloud Build**.
При пуше в ветку `main` автоматически собираются Docker-образы и деплоятся в **Cloud Run**.

**Требования к Cloud Build Trigger:**
Необходимо прописать Substitution variables (начинаются с `_`) в настройках триггера, соответствующие переменным из `.env` (например, `_GROQ_API_KEY`, `_DATABASE_URL` и т.д.).

---

### Разработано для Edton.ai

## 📖 Сценарии использования (Пользовательские роли)

**Роль: Соискатель (Обычный пользователь)**
1. **Регистрация и Вход:** Пользователь авторизуется в системе (Email/Пароль или OAuth).
2. **Шаг 1. Загрузка резюме:** Пользователь загружает PDF/DOCX файл своего существующего резюме. Система извлекает навыки, опыт и образование.
3. **Шаг 2. Добавление вакансии:** Пользователь вставляет текст или прямую ссылку на вакансию.
4. **Шаг 3. Анализ (Gap Analysis):** Пользователь получает отчет о том, чего не хватает в резюме для полного прохождения ATS по данной вакансии.
5. **Шаг 4. Адаптация:** Генерация новой улучшенной версии резюме, которая сохраняется в историю. Автоматическая генерация сопроводительного письма (Cover Letter).

## 🚑 Возможные ошибки и их решения (Troubleshooting)

| Ошибка / Проблема | Причина | Решение |
| :--- | :--- | :--- |
| `FastAPI: 500 Internal Server Error` при AI парсинге | Проблема с токенами или лимитами от LLM Provider (Groq/DeepSeek) | Убедитесь, что ключи в `.env` (например, `GROQ_API_KEY`) валидны и на аккаунте есть кредиты/лимиты. |
| База данных не отвечает (`Connection Refused`) | Supabase приостановил проект из-за неактивности или неверна строка подключения | Проверьте `DATABASE_URL` (должна быть через `postgresql+asyncpg://`). Зайдите в дашборд Supabase и "разбудите" проект (Restore project). |
| Ошибка сборки `docker-compose: backend build failed` | Отсутствие необходимых зависимостей в системе | Выполните `docker-compose build --no-cache`, чтобы пересобрать слои с нуля и скачать свежие пакеты. |
| Фронтенд: Белый экран или `CORS Error` | Неверный URL в переменной API | Убедитесь, что `VITE_API_URL` в `frontend/.env` указывает на `http://localhost:8000`. |
