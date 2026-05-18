"""Protocol interfaces for repository layer (Dependency Inversion Principle).

Services depend on these protocols, not on concrete repository implementations.
This enables easy mocking in tests and swapping implementations.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from uuid import UUID

# ── Resume ────────────────────────────────────────────────────────


@runtime_checkable
class IResumeRepository(Protocol):
    """Protocol for resume persistence operations."""

    async def get_by_hash(self, content_hash: str) -> Any: ...

    async def get_by_id(self, resume_id: UUID) -> Any: ...

    async def get_by_id_for_user(self, resume_id: UUID, user_id: str | UUID) -> Any: ...

    async def create(self, source_text: str, content_hash: str) -> Any: ...

    async def get_or_create(self, source_text: str, content_hash: str) -> Any: ...

    async def link_user_resume(self, user_id: str | UUID, resume_id: UUID) -> None: ...

    async def user_has_access(self, user_id: str | UUID, resume_id: UUID) -> bool: ...

    async def update_parsed_data(
        self, resume_id: UUID, parsed_data: dict[str, Any]
    ) -> Any: ...

    async def update_parsed_data_for_user(
        self, resume_id: UUID, user_id: str | UUID, parsed_data: dict[str, Any]
    ) -> Any: ...

    async def update_field(self, resume_id: UUID, field: str, value: Any) -> Any: ...


# ── Vacancy ───────────────────────────────────────────────────────


@runtime_checkable
class IVacancyRepository(Protocol):
    """Protocol for vacancy persistence operations."""

    async def get_by_hash(self, content_hash: str) -> Any: ...

    async def get_by_id(self, vacancy_id: UUID) -> Any: ...

    async def get_by_id_for_user(self, vacancy_id: UUID, user_id: str | UUID) -> Any: ...

    async def create(
        self,
        source_text: str,
        content_hash: str,
        source_url: str | None = None,
    ) -> Any: ...

    async def get_or_create(
        self,
        source_text: str,
        content_hash: str,
        source_url: str | None = None,
    ) -> Any: ...

    async def link_user_vacancy(self, user_id: str | UUID, vacancy_id: UUID) -> None: ...

    async def user_has_access(self, user_id: str | UUID, vacancy_id: UUID) -> bool: ...

    async def update_parsed_data(
        self, vacancy_id: UUID, parsed_data: dict[str, Any]
    ) -> Any: ...

    async def update_parsed_data_for_user(
        self, vacancy_id: UUID, user_id: str | UUID, parsed_data: dict[str, Any]
    ) -> Any: ...

    async def update_field(self, vacancy_id: UUID, field: str, value: Any) -> Any: ...


# ── AI Result (LLM cache) ────────────────────────────────────────


@runtime_checkable
class IAIResultRepository(Protocol):
    """Protocol for AI result cache operations."""

    async def get(self, operation: str, input_hash: str) -> Any: ...

    async def get_by_id(self, result_id: UUID) -> Any: ...

    async def save(
        self,
        operation: str,
        input_hash: str,
        output_json: dict[str, Any],
        provider: str | None = None,
        model: str | None = None,
        error: str | None = None,
    ) -> Any: ...


# ── Resume Version ───────────────────────────────────────────────


@runtime_checkable
class IResumeVersionRepository(Protocol):
    """Protocol for resume version operations."""

    async def create(
        self,
        resume_id: UUID,
        vacancy_id: UUID,
        text: str,
        change_log: list[dict],
        selected_checkbox_ids: list[str],
        analysis_id: UUID | None = None,
        parent_version_id: UUID | None = None,
        user_id: str | UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> Any: ...

    async def get_by_id(self, version_id: UUID) -> Any: ...

    async def get_by_id_for_user(self, version_id: UUID, user_id: str | UUID) -> Any: ...

    async def get_versions_for_resume(
        self,
        resume_id: UUID,
        vacancy_id: UUID | None = None,
    ) -> list: ...

    async def get_latest_version(self, resume_id: UUID, vacancy_id: UUID) -> Any: ...


# ── Ideal Resume ─────────────────────────────────────────────────


@runtime_checkable
class IIdealResumeRepository(Protocol):
    """Protocol for ideal resume operations."""

    async def create(
        self,
        vacancy_id: UUID,
        vacancy_hash: str,
        text: str,
        generation_metadata: dict,
        options: dict,
        input_hash: str,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> Any: ...

    async def get_by_id(self, ideal_id: UUID) -> Any: ...

    async def get_by_input_hash(self, input_hash: str) -> Any: ...

    async def get_for_vacancy(self, vacancy_id: UUID) -> list: ...


# ── User Version ─────────────────────────────────────────────────


@runtime_checkable
class IUserVersionRepository(Protocol):
    """Protocol for user version operations."""

    async def create(
        self,
        type: str,
        resume_text: str,
        vacancy_text: str,
        result_text: str,
        user_id: str | UUID,
        title: str | None = None,
        change_log: list[dict] | None = None,
        selected_checkbox_ids: list[str] | None = None,
        analysis_id: UUID | None = None,
    ) -> Any: ...

    async def get_by_id(self, version_id: UUID, user_id: str | UUID) -> Any: ...

    async def list_versions(
        self,
        user_id: str | UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]: ...

    async def delete_by_id(self, version_id: UUID, user_id: str | UUID) -> bool: ...


# ── Feedback ─────────────────────────────────────────────────────


@runtime_checkable
class IFeedbackRepository(Protocol):
    """Protocol for feedback operations."""

    async def create(
        self,
        user_id: UUID,
        user_hash: str,
        metric_type: str,
        score: int,
        feedback_text: str,
        context_step: str | None = None,
        ui_variant: str | None = None,
        user_segment: str | None = None,
    ) -> Any: ...


# ── Billing / Subscriptions ───────────────────────────────────────


@runtime_checkable
class IBillingPlanRepository(Protocol):
    """Protocol for server-controlled plan and price reads."""

    async def list_active_plans(self) -> list[Any]: ...

    async def get_plan_by_code(self, code: str) -> Any: ...

    async def get_active_price(self, plan_code: str, provider: str) -> Any: ...


@runtime_checkable
class ISubscriptionRepository(Protocol):
    """Protocol for user-scoped subscription reads."""

    async def get_current_for_user(self, user_id: UUID) -> Any: ...

    async def get_by_provider_subscription_id(
        self,
        provider: str,
        provider_subscription_id: str,
    ) -> Any: ...


@runtime_checkable
class IUsageEventRepository(Protocol):
    """Protocol for append-only usage audit events."""

    async def create(
        self,
        user_id: UUID,
        feature_code: str,
        operation: str,
        quantity: int,
        status: str,
        idempotency_key: str | None = None,
        subscription_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any: ...


@runtime_checkable
class IPaymentEventRepository(Protocol):
    """Protocol for provider webhook/event idempotency."""

    async def get_by_provider_event_id(
        self,
        provider: str,
        provider_event_id: str,
    ) -> Any: ...
