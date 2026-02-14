"""Analysis link repository for linking resume-vacancy-analysis."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AnalysisLink


class AnalysisRepository:
    """Repository for AnalysisLink operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_ids(
        self,
        resume_id: UUID,
        vacancy_id: UUID,
    ) -> AnalysisLink | None:
        """Get analysis link by resume and vacancy IDs."""
        stmt = select(AnalysisLink).where(
            AnalysisLink.resume_id == resume_id,
            AnalysisLink.vacancy_id == vacancy_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def link(
        self,
        resume_id: UUID,
        vacancy_id: UUID,
        analysis_result_id: UUID,
    ) -> AnalysisLink:
        """Create link between resume, vacancy and analysis result."""
        link = AnalysisLink(
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            analysis_result_id=analysis_result_id,
        )
        self.session.add(link)
        await self.session.flush()
        return link
