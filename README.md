# EdTon.ai — AI Resume Adapter Service 🚀

**EdtonAI** — это веб-сервис для адаптации резюме под конкретные вакансии с использованием искусственного интеллекта (DeepSeek LLM).

> 📚 **Detailed Documentation**:
> - [Backend Overview](docs/backend/overview.md)
> - [Frontend Overview](docs/frontend/overview.md)
> - [Frontend Development Guide](frontend/DEVELOPMENT.md)

Проект включает в себя парсинг резюме/вакансий, анализ соответствия, генерацию улучшений и управление историей версий.

## 🛠️ Технологический стек

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** (стилизация)
- **TanStack Query** (управление состоянием API)
- **Supabase Auth** (аутентификация пользователей)
- **React Router**
- **Nginx** (в Docker контейнере)

### Backend
- **FastAPI** (Python 3.11+)
- **SQLAlchemy 2.0** + **AsyncPG** (работа с БД)
- **PostgreSQL** (управляемая Supabase база данных)
- **DeepSeek API** (LLM провайдер)
- **PyJWT** (верификация токенов Supabase)

### Infrastructure
- **Google Cloud Run** (бессерверный деплой)
- **Cloud Build** (CI/CD пайплайны)
- **Docker** (контейнеризация)

---

## 🚀 Быстрый старт (Локально)

### Требования
- **Docker** и **Docker Compose** (рекомендуется)
- Или: **Python 3.11+**, **Node.js 18+**
- **Supabase** проект (URL и Anon Key)
- **DeepSeek API Key**

### Установка и запуск

1. **Клонируй репозиторий:**
   ```bash
   git clone <repo-url>
   cd edtonai
   ```

2. **Настрой переменные окружения:**
   Создай `.env` файл в корне проекта (скопируй из `.env.example`):
   ```bash
   cp .env.example .env
   ```
   **Важно:** Укажи в `.env`:
   - `DEEPSEEK_API_KEY`: Твой ключ от DeepSeek.
   - `VITE_SUPABASE_URL`: URL твоего Supabase проекта.
   - `VITE_SUPABASE_ANON_KEY`: Anon ключ Supabase.
   - `SUPABASE_JWT_SECRET`: JWT Secret из настроек API Supabase (для backend auth).
   - `POSTGRES_PASSWORD`: Пароль от базы данных.

3. **Запусти через Docker Compose (Backend + Frontend):**
   ```bash
   docker-compose up -d --build
   ```

4. **Открой приложение:**
   - **Frontend:** [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Запуск вручную (для разработки)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Убедись, что переменные из .env доступны (или создай backend/.env)
python main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## ☁️ Деплой (Google Cloud Run)

Проект настроен на автоматический деплой через **Google Cloud Build** при пуше в ветку `main`.

### CI/CD Setup
В настройках триггера Cloud Build должна быть добавлена переменная:
- `_SUPABASE_JWT_SECRET`: (Твой реальный JWT секрет)

### Ручной деплой
```bash
# Backend
gcloud run deploy edtonai-backend --source . --env-vars-file backend.env

# Frontend
gcloud run deploy edtonai-frontend --source . --update-env-vars "BACKEND_URL=https://your-backend-url"
```

---

## 🔒 Безопасность и База Данных

- **Аутентификация:** Используется Supabase Auth (Frontend).
- **Авторизация (Backend):** JWT токены проверяются на бэкенде.
- **Изоляция данных:** Включена **Row Level Security (RLS)** в PostgreSQL. Каждый пользователь имеет доступ только к своей истории (`user_id`).

### Миграции
Для применения схемы базы данных используйте SQL скрипт:
- [`docs/supabase_migration.sql`](docs/supabase_migration.sql) — создание таблиц, индексов и политик безопасности.

---

## ✨ Основные функции

1. **Workspace**:
   - Парсинг текста резюме и вакансии.
   - Анализ соответствия (Match Score).
   - Выбор улучшений (чекбоксы).
   - Адаптация (Rewrite) резюме.

2. **История версий**:
   - Автоматическое сохранение версий.
   - Просмотр деталей.
   - Сравнение (Diff) версий.

3. **Экспорт**:
   - Генерация PDF (в планах).
   - Копирование текста.
