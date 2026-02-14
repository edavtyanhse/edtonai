"""Repository layer for database operations."""

from .ai_result import AIResultRepository
from .analysis import AnalysisRepository
from .ideal_resume import IdealResumeRepository
from .resume import ResumeRepository
from .resume_version import ResumeVersionRepository
from .user_version import UserVersionRepository
from .vacancy import VacancyRepository

__all__ = [
    # Stage 1
    "ResumeRepository",
    "VacancyRepository",
    "AIResultRepository",
    "AnalysisRepository",
    # Stage 2
    "ResumeVersionRepository",
    "IdealResumeRepository",
    # Stage 3
    "UserVersionRepository",
]
