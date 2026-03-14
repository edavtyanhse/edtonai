"""Domain layer — internal DTOs (dataclasses) for inter-service communication."""

from .adapt import AdaptResumeResult, SelectedImprovement
from .analysis import FullAnalysisResult
from .cover_letter import CoverLetterResult
from .ideal import IdealResumeResult
from .match import MatchAnalysisResult
from .resume import ResumeParseResult
from .vacancy import VacancyParseResult

__all__ = [
    "ResumeParseResult",
    "VacancyParseResult",
    "MatchAnalysisResult",
    "FullAnalysisResult",
    "SelectedImprovement",
    "AdaptResumeResult",
    "IdealResumeResult",
    "CoverLetterResult",
]
