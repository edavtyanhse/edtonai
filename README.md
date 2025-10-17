# EdTon.ai monorepo

EdTon.ai — ассистент, который помогает адаптировать резюме и сопроводительные письма под конкретные вакансии. Репозиторий содержит фронтенд на Vite + React, FastAPI-бэкенд и инфраструктуру для локальной разработки.

## Структура репозитория

- `frontend/` — Vite-приложение с экраном загрузки, анализа и генерации документов.
- `backend/` — FastAPI-приложение, которое вызывает DeepSeek (OpenAI-совместимый API) и выполняет базовые эвристики.
- `db/` — SQL-миграции для локальной PostgreSQL.
- `docker-compose.yml` — сервис базы данных для локального запуска.

## Подготовка окружения

1. Склонируйте репозиторий и перейдите в корень проекта.
2. Запустите PostgreSQL:

   ```bash
   docker compose up -d
   ```

   После старта база будет доступна на `postgresql://edton:edton@localhost:5432/edton`. Скрипт `db/001_init.sql` создаёт таблицы при первом запуске.

## Backend (FastAPI)

1. Перейдите в директорию `backend/` и создайте виртуальное окружение:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Создайте файл `.env`, используя пример:

   ```bash
   cp .env.example .env
   ```

   Обновите `AI_API_KEY` значением ключа DeepSeek. При необходимости скорректируйте `DATABASE_URL`.

4. Запустите сервер разработки:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Проверки здоровья:

   - `GET http://localhost:8000/health` → `{ "ok": true }`
   - `GET http://localhost:8000/db/health` → `{ "db_ok": true }`

6. Основные эндпоинты:

   - `POST /api/parse` — принимает файл (PDF/DOCX/TXT) и возвращает распознанный UTF-8 текст резюме.
     Используется фронтендом для корректного парсинга русскоязычных документов перед анализом.

   - `POST /api/analyze`

     ```json
     {
       "resume_text": "string",
       "vacancy_text": "string",
       "role": "optional"
     }
     ```

     Ответ:

     ```json
     {
       "match_score": 0.0,
       "matched_skills": [],
       "missing_skills": [],
       "tips": "string"
     }
     ```

   - `POST /api/generate`

     ```json
     {
       "resume_text": "string",
       "vacancy_text": "string",
       "target_role": "optional"
     }
     ```

     Ответ:

     ```json
     {
       "improved_resume": "string",
       "cover_letter": "string",
       "ats_score": 0.0
     }
     ```

## Frontend (Vite + React)

1. Перейдите в `frontend/` и установите зависимости:

   ```bash
   cd frontend
   npm install
   ```

2. Создайте файл `.env` из примера и укажите адрес бэкенда:

   ```bash
   cp .env.example .env
   # VITE_API_URL=http://localhost:8000
   ```

3. Запустите локальный сервер:

   ```bash
   npm run dev
   ```

4. Перейдите на `http://localhost:5173` и загрузите резюме + вакансию. Фронтенд выполнит реальные запросы к FastAPI, отобразит матчинг навыков, советы модели DeepSeek и предоставит адаптированное резюме с сопроводительным письмом.

   При загрузке PDF/DOCX резюме автоматически распознаётся на бэкенде через эндпоинт `/api/parse`, поэтому в текстовые поля попадает уже очищенный русский текст без бинарных артефактов.

## Полезные заметки

- CORS для разработки открыт на все источники. Для продакшна ограничьте домены в `backend/app/main.py`.
- Файлы `.env` и секреты исключены из Git — используйте `.env.example` для документирования настроек.
- Если нужно очистить состояние между шагами, очистите `sessionStorage` в браузере (фронтенд сохраняет результаты анализа и генерации в сессии).

## Лицензия

Проект распространяется под MIT License.
