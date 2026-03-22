"""Auth response schemas."""

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """Public user data."""

    id: str
    email: str
    is_email_verified: bool


class AuthResponse(BaseModel):
    """Login/register response with tokens."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
