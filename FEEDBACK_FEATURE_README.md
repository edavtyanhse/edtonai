# Feedback Collection Feature

## Overview
Временная функция сбора отзывов от пользователей. Спроектирована для лёгкого отключения и удаления.

## Как работает
- Баннер на главной странице (`LandingPage`) — ведёт на `/login` для неавторизованных
- Баннер на `HomePage` — открывает модал для авторизованных пользователей
- Модал на `Step4Improvement` — можно открыть вручную (авто-показ отключён)
- Отзывы сохраняются в БД с email пользователя
- Требуется авторизация для отправки

## Конфигурация

### Отключение функции
Установить переменные окружения:
```bash
# Backend
FEEDBACK_COLLECTION_ENABLED=false

# Frontend  
VITE_FEEDBACK_ENABLED=false
```

## Полная инструкция по удалению

### Backend
1. Удалить файлы:
   - `backend/models/feedback.py`
   - `backend/schemas/feedback.py`
   - `backend/repositories/feedback.py`
   - `backend/api/v1/feedback.py`
   - `backend/migrations/004_add_feedback_table.sql`

2. Отредактировать `backend/api/v1/__init__.py`:
   - Удалить: `from .feedback import router as feedback_router`
   - Удалить: `router.include_router(feedback_router)`

3. Отредактировать `backend/core/config.py`:
   - Удалить: `feedback_collection_enabled: bool = True`

4. Удалить таблицу из БД:
   ```sql
   DROP TABLE feedback;
   ```

### Frontend
1. Удалить папку целиком:
   - `frontend/src/features/feedback/`

2. Отредактировать `frontend/src/pages/LandingPage.tsx`:
   - Удалить импорт:
     ```typescript
     import { FeedbackBanner } from '@/features/feedback'
     ```
   - Удалить импорт `useNavigate` из `react-router-dom` (если больше не используется)
   - Удалить блок с баннером:
     ```tsx
     {/* FEEDBACK FEATURE - remove this block to disable */}
     <div className="max-w-5xl mx-auto px-6 py-4">
         <FeedbackBanner onClick={() => navigate('/login')} />
     </div>
     ```

3. Отредактировать `frontend/src/pages/HomePage.tsx`:
   - Удалить импорт:
     ```typescript
     import { FeedbackBanner, FeedbackModal, useFeedback } from '@/features/feedback'
     ```
   - Удалить хук: `const feedback = useFeedback()`
   - Удалить компонент `<FeedbackBanner />`
   - Удалить компонент `<FeedbackModal />`

4. Отредактировать `frontend/src/pages/wizard/Step4Improvement.tsx`:
   - Удалить импорт:
     ```typescript
     import { FeedbackModal, useFeedback } from '@/features/feedback'
     ```
   - Удалить хук: `const feedback = useFeedback()`
   - Удалить компонент `<FeedbackModal />` (в конце файла)

5. Удалить этот файл:
   - `FEEDBACK_FEATURE_README.md`

## Добавленные файлы

### Backend
- `backend/models/feedback.py` — SQLAlchemy модель
- `backend/schemas/feedback.py` — Pydantic схемы
- `backend/repositories/feedback.py` — работа с БД
- `backend/api/v1/feedback.py` — API endpoint `POST /v1/feedback`
- `backend/migrations/004_add_feedback_table.sql` — миграция БД
- Изменён: `backend/core/config.py` (добавлен флаг `feedback_collection_enabled`)
- Изменён: `backend/api/v1/__init__.py` (подключён роутер)

### Frontend
- `frontend/src/features/feedback/` — все компоненты фидбека
  - `config.ts` — конфигурация (тексты, флаг включения)
  - `api.ts` — отправка отзыва на backend
  - `FeedbackModal.tsx` — модальное окно с формой
  - `FeedbackBanner.tsx` — баннер-приглашение
  - `useFeedback.ts` — React хук управления состоянием
  - `index.ts` — экспорты
- Изменён: `frontend/src/pages/LandingPage.tsx` (добавлен баннер)
- Изменён: `frontend/src/pages/HomePage.tsx` (добавлены баннер + модал)
- Изменён: `frontend/src/pages/wizard/Step4Improvement.tsx` (добавлен модал)

## Схема БД
```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR NOT NULL,
    feedback_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```
