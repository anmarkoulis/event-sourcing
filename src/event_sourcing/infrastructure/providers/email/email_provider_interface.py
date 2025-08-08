from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EmailProviderInterface(ABC):
    """Abstract interface for email providers"""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """Send an email using the provider.

        :param to_email: Recipient email address.
        :param subject: Email subject line.
        :param body: Email body content.
        :param from_email: Sender email address (optional).
        :param kwargs: Additional provider-specific parameters.
        :return: True if email was sent successfully, False otherwise.
        """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this email provider.

        :return: Provider name as string.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the email provider is available and configured.

        :return: True if provider is available, False otherwise.
        """

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration (optional method).

        :return: Dictionary containing provider configuration.
        """
        return {}
