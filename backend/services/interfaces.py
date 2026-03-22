"""Protocol interfaces for service layer (Dependency Inversion Principle).

Higher-level services (OrchestratorService, AdaptResumeService) depend on
these protocols instead of concrete implementations.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from backend.domain.adapt import AdaptResumeResult, SelectedImprovement
from backend.domain.cover_letter import CoverLetterResult
from backend.domain.ideal import IdealResumeResult
from backend.domain.match import MatchAnalysisResult
from backend.domain.resume import ResumeParseResult
from backend.domain.vacancy import VacancyParseResult


@runtime_checkable
class IResumeService(Protocol):
    """Protocol for resume parsing service."""

    async def parse_and_cache(self, resume_text: str) -> ResumeParseResult: ...


@runtime_checkable
class IVacancyService(Protocol):
    """Protocol for vacancy parsing service."""

    async def parse_and_cache(
        self,
        vacancy_text: str,
        source_url: str | None = None,
    ) -> VacancyParseResult: ...


@runtime_checkable
class IMatchService(Protocol):
    """Protocol for match analysis service."""

    async def analyze_and_cache(
        self,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
    ) -> MatchAnalysisResult: ...

    async def analyze_with_context(
        self,
        parsed_resume: dict[str, Any],
        parsed_vacancy: dict[str, Any],
        original_analysis: dict[str, Any],
        applied_checkbox_ids: list[str],
    ) -> MatchAnalysisResult: ...


@runtime_checkable
class IAdaptResumeService(Protocol):
    """Protocol for resume adaptation service."""

    async def adapt_and_version(
        self,
        resume_text: str | None = None,
        resume_id: UUID | None = None,
        vacancy_text: str | None = None,
        vacancy_id: UUID | None = None,
        selected_improvements: list[SelectedImprovement] | None = None,
        selected_checkbox_ids: list[str] | None = None,
        base_version_id: UUID | None = None,
        options: dict[str, Any] | None = None,
    ) -> AdaptResumeResult: ...


@runtime_checkable
class IIdealResumeService(Protocol):
    """Protocol for ideal resume generation service."""

    async def generate_ideal(
        self,
        vacancy_text: str | None = None,
        vacancy_id: UUID | None = None,
        options: dict[str, Any] | None = None,
    ) -> IdealResumeResult: ...


@runtime_checkable
class ICoverLetterService(Protocol):
    """Protocol for cover letter generation service."""

    async def generate_cover_letter(
        self,
        resume_version_id: UUID,
        user_id: str | UUID,
        options: dict[str, Any] | None = None,
    ) -> CoverLetterResult: ...


@runtime_checkable
class IOrchestratorService(Protocol):
    """Protocol for full analysis pipeline orchestrator."""

    async def run_analysis(
        self,
        resume_text: str,
        vacancy_text: str,
    ) -> Any: ...
