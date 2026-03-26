"""V1 API router."""

from fastapi import APIRouter

from .adapt import router as adapt_router
from .analytics import router as analytics_router
from .cover_letter import router as cover_letter_router
from .feedback import router as feedback_router  # FEEDBACK FEATURE - remove to disable
from .ideal import router as ideal_router
from .match import router as match_router
from .resumes import router as resumes_router
from .vacancies import router as vacancies_router
from .versions import router as versions_router

router = APIRouter(prefix="/v1")

# Stage 1 routes
router.include_router(resumes_router)
router.include_router(vacancies_router)
router.include_router(match_router)

# Stage 2 routes
router.include_router(adapt_router)
router.include_router(ideal_router)
router.include_router(cover_letter_router)

# Stage 3 routes
router.include_router(versions_router)

# Stage 4 routes (analytics & feedback)
router.include_router(analytics_router)

# Feedback feature (controlled by settings.feedback_collection_enabled)
# TO REMOVE: Delete this line and backend/api/v1/feedback.py
router.include_router(feedback_router)
