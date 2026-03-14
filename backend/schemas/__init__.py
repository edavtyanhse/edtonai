"""Pydantic schemas for API request/response.

Backward-compatible façade: re-exports every schema from
common/, requests/ and responses/ sub-packages so that existing
`from backend.schemas import Xyz` imports keep working.
"""

# ── common (shared between requests & responses) ──────────────────
from .common import (
    AdaptResumeOptions,
    ChangeLogEntry,
    CoverLetterStructure,
    IdealResumeMetadata,
    IdealResumeOptions,
    SelectedImprovementSchema,
)

# ── requests ──────────────────────────────────────────────────────
from .requests import (
    AdaptResumeRequest,
    CoverLetterRequest,
    FeedbackCreate,
    IdealResumeRequest,
    MatchAnalyzeRequest,
    ResumeParseRequest,
    ResumePatchRequest,
    VacancyParseRequest,
    VacancyPatchRequest,
    VersionCreateRequest,
)

# ── responses ─────────────────────────────────────────────────────
from .responses import (
    AdaptResumeResponse,
    CoverLetterResponse,
    FeedbackResponse,
    IdealResumeResponse,
    MatchAnalyzeResponse,
    ResumeDetailResponse,
    ResumeParseResponse,
    VacancyDetailResponse,
    VacancyParseResponse,
    VersionDetailResponse,
    VersionItemResponse,
    VersionListResponse,
)

__all__ = [
    # common
    "AdaptResumeOptions",
    "ChangeLogEntry",
    "CoverLetterStructure",
    "IdealResumeMetadata",
    "IdealResumeOptions",
    "SelectedImprovementSchema",
    # requests
    "ResumeParseRequest",
    "ResumePatchRequest",
    "VacancyParseRequest",
    "VacancyPatchRequest",
    "MatchAnalyzeRequest",
    "AdaptResumeRequest",
    "IdealResumeRequest",
    "CoverLetterRequest",
    "VersionCreateRequest",
    "FeedbackCreate",
    # responses
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
