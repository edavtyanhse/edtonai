"""Vacancy repository for database operations."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import VacancyRaw


class VacancyRepository:
    """Repository for VacancyRaw operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_hash(self, content_hash: str) -> Optional[VacancyRaw]:
        """Get vacancy by content hash."""
        stmt = select(VacancyRaw).where(VacancyRaw.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, vacancy_id: UUID) -> Optional[VacancyRaw]:
        """Get vacancy by ID."""
        stmt = select(VacancyRaw).where(VacancyRaw.id == vacancy_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        source_text: str,
        content_hash: str,
        source_url: Optional[str] = None,
    ) -> VacancyRaw:
        """Create new vacancy record."""
        vacancy = VacancyRaw(
            source_text=source_text,
            content_hash=content_hash,
            source_url=source_url,
        )
        self.session.add(vacancy)
        await self.session.flush()
        return vacancy

    async def update_parsed_data(
        self, vacancy_id: UUID, parsed_data: Dict[str, Any]
    ) -> Optional[VacancyRaw]:
        """Update parsed data columns for a vacancy."""
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy is None:
            return None
        # Use helper method to set all parsed fields
        vacancy.set_parsed_data(parsed_data)
        vacancy.parsed_at = datetime.utcnow()
        await self.session.flush()
        return vacancy

    async def update_field(
        self, vacancy_id: UUID, field: str, value: Any
    ) -> Optional[VacancyRaw]:
        """Update a single parsed field for a vacancy."""
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy is None:
            return None
        
        allowed_fields = [
            "job_title", "company", "employment_type", "location",
            "required_skills", "preferred_skills", "experience_requirements",
            "responsibilities", "ats_keywords"
        ]
        if field not in allowed_fields:
            raise ValueError(f"Field {field} is not allowed")
        
        setattr(vacancy, field, value)
        vacancy.parsed_at = datetime.utcnow()
        await self.session.flush()
        return vacancy
