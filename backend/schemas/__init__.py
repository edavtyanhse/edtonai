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
    AnalyticsEventCreate,
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
    AnalyticsEventAcceptedResponse,
    BillingAccountResponse,
    BillingPlanListResponse,
    BillingPlanResponse,
    BillingPriceResponse,
    CoverLetterResponse,
    CurrentSubscriptionResponse,
    FeedbackResponse,
    IdealResumeResponse,
    MatchAnalyzeResponse,
    PlanEntitlementResponse,
    ResumeDetailResponse,
    ResumeParseResponse,
    UsageFeatureResponse,
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
    "AnalyticsEventCreate",
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
    "AnalyticsEventAcceptedResponse",
    "BillingAccountResponse",
    "BillingPlanListResponse",
    "BillingPlanResponse",
    "BillingPriceResponse",
    "CurrentSubscriptionResponse",
    "PlanEntitlementResponse",
    "UsageFeatureResponse",
    "IdealResumeResponse",
    "CoverLetterResponse",
    "VersionItemResponse",
    "VersionDetailResponse",
    "VersionListResponse",
    "FeedbackResponse",
]
