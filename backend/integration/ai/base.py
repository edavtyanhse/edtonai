from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract AI provider capable of returning JSON responses."""

    @abstractmethod
    async def generate_json(
        self, prompt: str, prompt_name: str | None = None
    ) -> dict[str, Any]:
        """Generate a JSON dictionary for the given prompt."""
        raise NotImplementedError
