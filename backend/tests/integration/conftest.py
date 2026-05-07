"""Shared fixtures for integration tests (HTTP client, DB, etc.)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from backend.auth.jwt import create_access_token
from backend.core.config import settings
from backend.main import app, container

TEST_USER_ID = uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FakeResumeRecord:
    id: UUID
    source_text: str
    content_hash: str
    created_at: datetime = field(default_factory=_utcnow)
    parsed_at: datetime | None = None
    personal_info: dict | None = None
    summary: str | None = None
    skills: list = field(default_factory=list)
    work_experience: list = field(default_factory=list)
    education: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    languages: list = field(default_factory=list)
    raw_sections: dict = field(default_factory=dict)


@dataclass
class FakeVacancyRecord:
    id: UUID
    source_text: str
    content_hash: str
    source_url: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    parsed_at: datetime | None = None
    job_title: str | None = None
    company: str | None = None
    employment_type: str | None = None
    location: str | None = None
    required_skills: list = field(default_factory=list)
    preferred_skills: list = field(default_factory=list)
    experience_requirements: dict | None = None
    responsibilities: list = field(default_factory=list)
    ats_keywords: list = field(default_factory=list)


class InMemoryResumeRepo:
    def __init__(self) -> None:
        self.by_hash: dict[str, FakeResumeRecord] = {}
        self.by_id: dict[UUID, FakeResumeRecord] = {}
        self.user_links: set[tuple[str, UUID]] = set()
        self.user_overrides: dict[tuple[str, UUID], dict] = {}

    @staticmethod
    def _with_override(record: FakeResumeRecord, override: dict | None):
        if override is None:
            return record
        snapshot = SimpleNamespace(**record.__dict__)
        for key, value in override.items():
            setattr(snapshot, key, value)
        snapshot.parsed_at = datetime.now(timezone.utc)
        return snapshot

    async def get_by_hash(self, content_hash: str):
        return self.by_hash.get(content_hash)

    async def get_by_id(self, resume_id: UUID):
        return self.by_id.get(resume_id)

    async def get_by_id_for_user(self, resume_id: UUID, user_id: str):
        if (user_id, resume_id) not in self.user_links:
            return None
        record = self.by_id.get(resume_id)
        if record is None:
            return None
        return self._with_override(record, self.user_overrides.get((user_id, resume_id)))

    async def create(self, source_text: str, content_hash: str):
        record = FakeResumeRecord(
            id=uuid4(), source_text=source_text, content_hash=content_hash
        )
        self.by_hash[content_hash] = record
        self.by_id[record.id] = record
        return record

    async def get_or_create(self, source_text: str, content_hash: str):
        existing = await self.get_by_hash(content_hash)
        if existing:
            return existing
        return await self.create(source_text, content_hash)

    async def link_user_resume(self, user_id: str, resume_id: UUID) -> None:
        self.user_links.add((user_id, resume_id))

    async def user_has_access(self, user_id: str, resume_id: UUID) -> bool:
        return (user_id, resume_id) in self.user_links

    async def update_parsed_data(self, resume_id: UUID, parsed_data: dict):
        record = await self.get_by_id(resume_id)
        if record is None:
            return None
        for key, value in parsed_data.items():
            setattr(record, key, value)
        record.parsed_at = datetime.now(timezone.utc)
        return record

    async def update_parsed_data_for_user(
        self, resume_id: UUID, user_id: str, parsed_data: dict
    ):
        record = await self.get_by_id_for_user(resume_id, user_id)
        if record is None:
            return None
        self.user_overrides[(user_id, resume_id)] = parsed_data
        return self._with_override(self.by_id[resume_id], parsed_data)


class InMemoryVacancyRepo:
    def __init__(self) -> None:
        self.by_hash: dict[str, FakeVacancyRecord] = {}
        self.by_id: dict[UUID, FakeVacancyRecord] = {}
        self.user_links: set[tuple[str, UUID]] = set()
        self.user_overrides: dict[tuple[str, UUID], dict] = {}

    @staticmethod
    def _with_override(record: FakeVacancyRecord, override: dict | None):
        if override is None:
            return record
        snapshot = SimpleNamespace(**record.__dict__)
        for key, value in override.items():
            setattr(snapshot, key, value)
        snapshot.parsed_at = datetime.now(timezone.utc)
        return snapshot

    async def get_by_hash(self, content_hash: str):
        return self.by_hash.get(content_hash)

    async def get_by_id(self, vacancy_id: UUID):
        return self.by_id.get(vacancy_id)

    async def get_by_id_for_user(self, vacancy_id: UUID, user_id: str):
        if (user_id, vacancy_id) not in self.user_links:
            return None
        record = self.by_id.get(vacancy_id)
        if record is None:
            return None
        return self._with_override(record, self.user_overrides.get((user_id, vacancy_id)))

    async def create(
        self, source_text: str, content_hash: str, source_url: str | None = None
    ):
        record = FakeVacancyRecord(
            id=uuid4(),
            source_text=source_text,
            content_hash=content_hash,
            source_url=source_url,
        )
        self.by_hash[content_hash] = record
        self.by_id[record.id] = record
        return record

    async def get_or_create(
        self, source_text: str, content_hash: str, source_url: str | None = None
    ):
        existing = await self.get_by_hash(content_hash)
        if existing:
            return existing
        return await self.create(source_text, content_hash, source_url)

    async def link_user_vacancy(self, user_id: str, vacancy_id: UUID) -> None:
        self.user_links.add((user_id, vacancy_id))

    async def user_has_access(self, user_id: str, vacancy_id: UUID) -> bool:
        return (user_id, vacancy_id) in self.user_links

    async def update_parsed_data(self, vacancy_id: UUID, parsed_data: dict):
        record = await self.get_by_id(vacancy_id)
        if record is None:
            return None
        for key, value in parsed_data.items():
            setattr(record, key, value)
        record.parsed_at = datetime.now(timezone.utc)
        return record

    async def update_parsed_data_for_user(
        self, vacancy_id: UUID, user_id: str, parsed_data: dict
    ):
        record = await self.get_by_id_for_user(vacancy_id, user_id)
        if record is None:
            return None
        self.user_overrides[(user_id, vacancy_id)] = parsed_data
        return self._with_override(self.by_id[vacancy_id], parsed_data)


class InMemoryAIResultRepo:
    def __init__(self) -> None:
        self.by_key: dict[tuple[str, str], SimpleNamespace] = {}
        self.by_id: dict[UUID, SimpleNamespace] = {}

    async def get(self, operation: str, input_hash: str):
        return self.by_key.get((operation, input_hash))

    async def get_by_id(self, result_id: UUID):
        return self.by_id.get(result_id)

    async def save(
        self,
        operation: str,
        input_hash: str,
        output_json: dict,
        provider: str | None = None,
        model: str | None = None,
        error: str | None = None,
    ):
        result = SimpleNamespace(
            id=uuid4(),
            operation=operation,
            input_hash=input_hash,
            output_json=output_json,
            provider=provider,
            model=model,
            error=error,
            created_at=datetime.now(timezone.utc),
        )
        self.by_key[(operation, input_hash)] = result
        self.by_id[result.id] = result
        return result


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for tests that don't need real AI calls."""
    provider = AsyncMock()
    provider.provider_name = "mock-provider"
    provider.model = "mock-model"
    return provider


@pytest.fixture
async def client(mock_ai_provider):
    """Async HTTP client for testing FastAPI endpoints without a real DB."""
    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    fake_resume_repo = InMemoryResumeRepo()
    fake_vacancy_repo = InMemoryVacancyRepo()
    fake_ai_result_repo = InMemoryAIResultRepo()
    access_token = create_access_token(
        user_id=TEST_USER_ID,
        email="test@example.com",
        secret=settings.jwt_secret_key,
    )

    with (
        container.session.override(providers.Object(mock_session)),
        container.resume_repo.override(providers.Object(fake_resume_repo)),
        container.vacancy_repo.override(providers.Object(fake_vacancy_repo)),
        container.ai_result_repo.override(providers.Object(fake_ai_result_repo)),
        container.ai_provider_parsing.override(mock_ai_provider),
        container.ai_provider_reasoning.override(mock_ai_provider),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as ac:
            yield ac


@pytest.fixture
async def unauth_client(mock_ai_provider):
    """Async HTTP client without Authorization header for auth hardening tests."""
    mock_session = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    with container.session.override(providers.Object(mock_session)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
