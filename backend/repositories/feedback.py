"""Feedback repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.feedback import Feedback


class FeedbackRepository:
    """Repository for feedback operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_email: str, feedback_text: str) -> Feedback:
        """Create new feedback entry."""
        feedback = Feedback(
            user_email=user_email,
            feedback_text=feedback_text
        )
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback
