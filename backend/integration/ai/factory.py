from typing import Literal

from backend.core.config import settings
from backend.integration.ai.base import AIProvider
from backend.integration.ai.deepseek import DeepSeekProvider
from backend.integration.ai.groq import GroqProvider

TaskType = Literal["parsing", "reasoning"]

def get_ai_provider(task_type: TaskType = "reasoning") -> AIProvider:
    """Factory to get the configured AI provider instance for a specific task."""

    # Determine provider name based on task type
    if task_type == "parsing":
        provider_name = settings.ai_provider_parsing.lower()
        groq_model = settings.groq_model_parsing
    else:
        provider_name = settings.ai_provider_reasoning.lower()
        groq_model = settings.groq_model_reasoning

    if provider_name == "groq":
        return GroqProvider(model=groq_model)
    elif provider_name == "deepseek":
        return DeepSeekProvider()
    else:
         raise ValueError(f"Unsupported AI provider: {provider_name}")
