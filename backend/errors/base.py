"""Base application error class."""


class AppError(Exception):
    """Base class for all application-level errors.

    Attributes:
        message: Human-readable error description.
        status_code: Suggested HTTP status code for this error type.
    """

    status_code: int = 500

    def __init__(self, message: str = "Internal server error") -> None:
        self.message = message
        super().__init__(message)
