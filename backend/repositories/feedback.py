"""Feedback repository for database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.feedback import Feedback


class FeedbackRepository:
    """Repository for feedback operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_email: str,
        metric_type: str,
        score: int,
        feedback_text: str,
        context_step: str | None = None,
        ui_variant: str | None = None,
        user_segment: str | None = None,
    ) -> Feedback:
        """Create new feedback entry."""
        feedback = Feedback(
            user_email=user_email,
            metric_type=metric_type,
            score=score,
            feedback_text=feedback_text,
            context_step=context_step,
            ui_variant=ui_variant,
            user_segment=user_segment,
        )
        self.session.add(feedback)
        await self.session.flush()
        return feedback
