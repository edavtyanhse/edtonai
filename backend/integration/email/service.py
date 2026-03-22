"""Email service — sends verification and notification emails."""

import logging

from backend.integration.email.client import SmtpEmailClient
from backend.integration.email.templates import render_verification_email

logger = logging.getLogger(__name__)


class EmailService:
    """Application-level email operations."""

    def __init__(self, client: SmtpEmailClient) -> None:
        self._client = client

    async def send_verification_email(
        self,
        email: str,
        token: str,
        frontend_url: str,
    ) -> None:
        """Send verification email with link to frontend."""
        verify_url = f"{frontend_url.rstrip('/')}/verify-email?token={token}"
        subject, html = render_verification_email(verify_url)
        await self._client.send(to=email, subject=subject, html_body=html)
