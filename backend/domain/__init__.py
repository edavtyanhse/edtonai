"""Domain layer — internal DTOs (dataclasses) for inter-service communication."""

from .adapt import AdaptResumeResult, SelectedImprovement
from .analysis import FullAnalysisResult
from .analytics import AnalyticsEventAccepted
from .cover_letter import CoverLetterResult
from .ideal import IdealResumeResult
from .match import MatchAnalysisResult
from .resume import ResumeDetailResult, ResumeParseResult
from .vacancy import VacancyDetailResult, VacancyParseResult
from .version import VersionDetailResult, VersionItemResult, VersionListResult

__all__ = [
    "ResumeParseResult",
    "ResumeDetailResult",
    "VacancyParseResult",
    "VacancyDetailResult",
    "MatchAnalysisResult",
    "FullAnalysisResult",
    "SelectedImprovement",
    "AdaptResumeResult",
    "IdealResumeResult",
    "CoverLetterResult",
    "VersionItemResult",
    "VersionDetailResult",
    "VersionListResult",
    "AnalyticsEventAccepted",
]
