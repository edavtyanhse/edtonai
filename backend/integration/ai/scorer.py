"""Resume-vacancy semantic scorer using fine-tuned cross-encoder."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


class ResumeScorer:
    """Semantic scorer based on fine-tuned cross-encoder.

    Loads model lazily on first call and caches it in memory.
    Model is downloaded from HuggingFace Hub on first use.
    """

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading scorer model: {self.model_path}")
            self._model = CrossEncoder(self.model_path, max_length=512)
            logger.info("Scorer model loaded ✓")
        except Exception as e:
            logger.warning(f"Failed to load scorer model: {e}. Scorer disabled.")
            self._model = False  # Mark as failed so we don't retry

    def score(self, resume_text: str, vacancy_text: str) -> float | None:
        """Return semantic compatibility score 0-100, or None if scorer unavailable."""
        self._load()
        if not self._model:
            return None
        try:
            raw = self._model.predict([(resume_text[:3000], vacancy_text[:3000])])[0]
            prob = float(1 / (1 + np.exp(-raw)))
            return round(prob * 100, 1)
        except Exception as e:
            logger.warning(f"Scorer inference failed: {e}")
            return None
