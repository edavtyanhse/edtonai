"""Pydantic schemas for API request/response."""

from .resume import (
    ResumeParseRequest,
    ResumeParseResponse,
    ResumePatchRequest,
    ResumeDetailResponse,
)
from .vacancy import (
    VacancyParseRequest,
    VacancyParseResponse,
    VacancyPatchRequest,
    VacancyDetailResponse,
)
from .match import MatchAnalyzeRequest, MatchAnalyzeResponse
from .adapt import (
    AdaptResumeRequest,
    AdaptResumeResponse,
    AdaptResumeOptions,
    ChangeLogEntry,
)
from .ideal import (
    IdealResumeRequest,
    IdealResumeResponse,
    IdealResumeOptions,
    IdealResumeMetadata,
)
from .cover_letter import (
    CoverLetterRequest,
    CoverLetterResponse,
    CoverLetterStructure,
)
from .version import (
    VersionCreateRequest,
    VersionItemResponse,
    VersionDetailResponse,
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
