"""Response schemas — all API output contracts."""

from .adapt import AdaptResumeResponse
from .cover_letter import CoverLetterResponse
from .feedback import FeedbackResponse
from .ideal import IdealResumeResponse
from .match import MatchAnalyzeResponse
from .resume import ResumeDetailResponse, ResumeParseResponse
from .vacancy import VacancyDetailResponse, VacancyParseResponse
from .version import VersionDetailResponse, VersionItemResponse, VersionListResponse

__all__ = [
    "ResumeParseResponse",
    "ResumeDetailResponse",
    "VacancyParseResponse",
    "VacancyDetailResponse",
    "MatchAnalyzeResponse",
    "AdaptResumeResponse",
    "IdealResumeResponse",
    "CoverLetterResponse",
    "VersionItemResponse",
    "VersionDetailResponse",
    "VersionListResponse",
    "FeedbackResponse",
]
