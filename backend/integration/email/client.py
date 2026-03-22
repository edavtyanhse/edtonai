"""Async SMTP email client (Yandex)."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

logger = logging.getLogger(__name__)


class SmtpEmailClient:
    """Sends emails via SMTP (Yandex or other providers)."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email

    async def send(self, to: str, subject: str, html_body: str) -> None:
        """Send an email with HTML body."""
        message = MIMEMultipart("alternative")
        message["From"] = self._from_email
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                message,
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                use_tls=True,
            )
            logger.info("Email sent to %s: %s", to, subject)
        except Exception:
            logger.exception("Failed to send email to %s", to)
            raise
