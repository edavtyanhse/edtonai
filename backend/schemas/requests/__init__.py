"""Request schemas — all API input contracts."""

from .adapt import AdaptResumeRequest
from .analytics import AnalyticsEventCreate
from .cover_letter import CoverLetterRequest
from .feedback import FeedbackCreate
from .ideal import IdealResumeRequest
from .match import MatchAnalyzeRequest
from .resume import ResumeParseRequest, ResumePatchRequest
from .vacancy import VacancyParseRequest, VacancyPatchRequest
from .version import VersionCreateRequest

__all__ = [
    "ResumeParseRequest",
    "ResumePatchRequest",
    "VacancyParseRequest",
    "VacancyPatchRequest",
    "MatchAnalyzeRequest",
    "AdaptResumeRequest",
    "AnalyticsEventCreate",
    "IdealResumeRequest",
    "CoverLetterRequest",
    "VersionCreateRequest",
    "FeedbackCreate",
]
