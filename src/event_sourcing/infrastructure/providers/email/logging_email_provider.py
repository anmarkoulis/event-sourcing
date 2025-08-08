import logging
from typing import Any, Dict, Optional

from .email_provider_interface import EmailProviderInterface

logger = logging.getLogger(__name__)


class LoggingEmailProvider(EmailProviderInterface):
    """Logging implementation of email provider that logs emails instead of sending them"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the logging email provider.

        :param config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.default_from_email = self.config.get(
            "default_from_email", "noreply@example.com"
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """Log email details instead of sending.

        :param to_email: Recipient email address.
        :param subject: Email subject line.
        :param body: Email body content.
        :param from_email: Sender email address (optional).
        :param kwargs: Additional provider-specific parameters.
        :return: Always returns True to indicate "success".
        """
        actual_from_email = from_email or self.default_from_email

        logger.info(
            "EMAIL WOULD BE SENT:",
            extra={
                "email_provider": self.get_provider_name(),
                "from_email": actual_from_email,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "additional_params": kwargs,
            },
        )

        # Log in a more readable format for development
        logger.info(
            f"📧 Email logged (not sent):\n"
            f"  From: {actual_from_email}\n"
            f"  To: {to_email}\n"
            f"  Subject: {subject}\n"
            f"  Body: {body[:100]}{'...' if len(body) > 100 else ''}\n"
            f"  Additional params: {kwargs}"
        )

        return True

    def get_provider_name(self) -> str:
        """Get the name of this email provider.

        :return: Provider name as string.
        """
        return "logging"

    def is_available(self) -> bool:
        """Check if the email provider is available and configured.

        :return: Always returns True for logging provider.
        """
        return True

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration (optional method).

        :return: Dictionary containing provider configuration.
        """
        return {"default_from_email": self.default_from_email}
