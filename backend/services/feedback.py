"""Feedback service - validates and stores product feedback."""

import hashlib
import logging
from json import dumps
from typing import Any
from uuid import UUID

from backend.core.config import Settings
from backend.errors.business import UnprocessableEntityError
from backend.errors.integration import ServiceUnavailableError
from backend.repositories.interfaces import IFeedbackRepository

logger = logging.getLogger(__name__)


def _hash_user_identifier(identifier: str) -> str:
    return hashlib.sha256(identifier.strip().lower().encode("utf-8")).hexdigest()


class FeedbackService:
    """Application service for feedback collection."""

    def __init__(
        self,
        feedback_repo: IFeedbackRepository,
        settings: Settings,
    ) -> None:
        self.feedback_repo = feedback_repo
        self.settings = settings

    async def submit_feedback(
        self,
        user_id: UUID,
        metric_type: str,
        score: int,
        feedback_text: str,
        context_step: str | None = None,
        ui_variant: str | None = None,
        user_segment: str | None = None,
    ) -> Any:
        """Validate and persist authenticated feedback."""
        if not self.settings.feedback_collection_enabled:
            raise ServiceUnavailableError("Feedback collection is currently disabled")

        self._validate_score(metric_type, score)
        user_hash = _hash_user_identifier(str(user_id))

        feedback = await self.feedback_repo.create(
            user_id=user_id,
            user_hash=user_hash,
            metric_type=metric_type,
            score=score,
            feedback_text=feedback_text,
            context_step=context_step,
            ui_variant=ui_variant,
            user_segment=user_segment,
        )

        logger.info(
            "ANALYTICS_EVENT %s",
            dumps(
                {
                    "event_name": "feedback_submitted",
                    "metric_type": metric_type,
                    "score": score,
                    "context_step": context_step,
                    "ui_variant": ui_variant,
                    "user_segment": user_segment,
                    "user_hash": user_hash,
                    "feedback_id": feedback.id,
                },
                ensure_ascii=False,
            ),
        )
        return feedback

    @staticmethod
    def _validate_score(metric_type: str, score: int) -> None:
        if metric_type == "csat" and not (1 <= score <= 5):
            raise UnprocessableEntityError("CSAT score must be between 1 and 5")
        if metric_type == "nps" and not (0 <= score <= 10):
            raise UnprocessableEntityError("NPS score must be between 0 and 10")
