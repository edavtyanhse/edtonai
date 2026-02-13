# EdTon.ai — AI Resume Adapter Service 🚀

**EdtonAI** — это веб-сервис для умной адаптации резюме под конкретные вакансии с использованием искусственного интеллекта. Проект помогает кандидатам повысить шансы на прохождение ATS (Applicant Tracking Systems) и рекрутерского скрининга, генерируя оптимизированные версии резюме и сопроводительные письма.

## ✨ Основные возможности

*   **Умный парсинг**: Извлечение данных из резюме (PDF/DOCX/TXT) и вакансий (URL/Text) с помощью AI (Groq/Llama 3.1).
*   **Gap Analysis**: Детальный анализ соответствия резюме требованиям вакансии с выявлением недостающих навыков и ключевых слов (DeepSeek/Llama 3.3).
*   **AI Адаптация**: Автоматическое переписывание summary и bullet points опыта работы для закрытия найденных гэпов.
*   **Генерация Cover Letter**: Создание персонализированных сопроводительных писем под вакансию.
*   **История версий**: Полный контроль над версиями резюме, возможность отката и сравнения.

---

## 🏗️ Архитектура и Структура

Проект построен как монорепозиторий, разделенный на Frontend и Backend.

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
