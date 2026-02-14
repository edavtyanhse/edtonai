"""Pydantic schemas for API request/response."""

from .adapt import (
    AdaptResumeOptions,
    AdaptResumeRequest,
    AdaptResumeResponse,
    ChangeLogEntry,
)
from .cover_letter import (
    CoverLetterRequest,
    CoverLetterResponse,
    CoverLetterStructure,
)
from .ideal import (
    IdealResumeMetadata,
    IdealResumeOptions,
    IdealResumeRequest,
    IdealResumeResponse,
)
from .match import MatchAnalyzeRequest, MatchAnalyzeResponse
from .resume import (
    ResumeDetailResponse,
    ResumeParseRequest,
    ResumeParseResponse,
    ResumePatchRequest,
)
from .vacancy import (
    VacancyDetailResponse,
    VacancyParseRequest,
    VacancyParseResponse,
    VacancyPatchRequest,
)
from .version import (
    VersionCreateRequest,
    VersionDetailResponse,
    VersionItemResponse,
    VersionListResponse,
)

__all__ = [
    # Stage 1
    "ResumeParseRequest",
    "ResumeParseResponse",
    "ResumePatchRequest",
    "ResumeDetailResponse",
    "VacancyParseRequest",
    "VacancyParseResponse",
    "VacancyPatchRequest",
    "VacancyDetailResponse",
    "MatchAnalyzeRequest",
    "MatchAnalyzeResponse",
    # Stage 2
    "AdaptResumeRequest",
    "AdaptResumeResponse",
    "AdaptResumeOptions",
    "ChangeLogEntry",
    "IdealResumeRequest",
    "IdealResumeResponse",
    "IdealResumeOptions",
    "IdealResumeMetadata",
    "CoverLetterRequest",
    "CoverLetterResponse",
    "CoverLetterStructure",
    # Stage 3 - Versions
    "VersionCreateRequest",
    "VersionItemResponse",
    "VersionDetailResponse",
    "VersionListResponse",
]
