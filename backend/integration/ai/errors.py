class AIError(Exception):
    """Base class for AI-related errors."""


class AIRequestError(AIError):
    """Raised when the AI provider request fails."""


class AIResponseFormatError(AIError):
    """Raised when the AI response is not valid JSON after validation attempts."""
