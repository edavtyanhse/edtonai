# Feedback Collection Feature

## Overview
Temporary feature for collecting user feedback. Designed to be easily disabled and removed.

## How it works
- Shows banner on HomePage for manual feedback submission
- Auto-shows modal after resume analysis completion (once per user)
- Stores feedback in database with user email
- Requires authentication

## Configuration

### Disable Feature
Set environment variable:
```bash
# Backend
FEEDBACK_COLLECTION_ENABLED=false

# Frontend  
VITE_FEEDBACK_ENABLED=false
```

## Complete Removal Instructions

### Backend
1. Delete files:
   - `backend/models/feedback.py`
   - `backend/schemas/feedback.py`
   - `backend/repositories/feedback.py`
   - `backend/api/v1/feedback.py`
   - `backend/migrations/004_add_feedback_table.sql`

2. Edit `backend/api/v1/__init__.py`:
   - Remove: `from .feedback import router as feedback_router`
   - Remove: `router.include_router(feedback_router)`

3. Edit `backend/core/config.py`:
   - Remove: `feedback_collection_enabled: bool = True`

4. Drop database table:
   ```sql
   DROP TABLE feedback;
   ```

### Frontend
1. Delete folder:
   - `frontend/src/features/feedback/` (entire directory)

2. Edit `frontend/src/pages/HomePage.tsx`:
   - Remove imports:
     ```typescript
     import { FeedbackBanner, FeedbackModal, useFeedback } from '@/features/feedback'
     ```
   - Remove hook: `const feedback = useFeedback()`
   - Remove `<FeedbackBanner />` component
   - Remove `<FeedbackModal />` component

3. Edit `frontend/src/pages/wizard/Step4Improvement.tsx`:
   - Remove import:
     ```typescript
     import { FeedbackModal, useFeedback } from '@/features/feedback'
     ```
   - Remove hook: `const feedback = useFeedback()`
   - Remove `feedback.showFeedbackAuto()` call in `reanalyzeMutation.onSuccess`
   - Remove `<FeedbackModal />` component

## Files Added
### Backend
- `backend/models/feedback.py` - Database model
- `backend/schemas/feedback.py` - Pydantic schemas
- `backend/repositories/feedback.py` - Database operations
- `backend/api/v1/feedback.py` - API endpoint
- `backend/migrations/004_add_feedback_table.sql` - Database migration
- Modified: `backend/core/config.py` (added flag)
- Modified: `backend/api/v1/__init__.py` (added router)

### Frontend
- `frontend/src/features/feedback/` - All feedback components
  - `config.ts` - Feature configuration
  - `api.ts` - API integration
  - `FeedbackModal.tsx` - Modal component
  - `FeedbackBanner.tsx` - Banner component
  - `useFeedback.ts` - React hook
  - `index.ts` - Exports
- Modified: `frontend/src/pages/HomePage.tsx` (added banner + modal)
- Modified: `frontend/src/pages/wizard/Step4Improvement.tsx` (added auto-popup)

## Database Schema
```sql
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR NOT NULL,
    feedback_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```
