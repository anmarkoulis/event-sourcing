import logging
from typing import Any, Dict, Optional, Type

from .email_provider_interface import EmailProviderInterface

logger = logging.getLogger(__name__)


class EmailProviderFactory:
    """Factory for creating email providers"""

    _providers: Dict[str, Type[EmailProviderInterface]] = {}

    @classmethod
    def register_provider(
        cls, provider_name: str, provider_class: Type[EmailProviderInterface]
    ) -> None:
        """Register a provider class with the factory.

        :param provider_name: Name of the provider to register.
        :param provider_class: Provider class to register.
        """
        cls._providers[provider_name.lower()] = provider_class
        logger.info(f"Registered email provider: {provider_name}")

    @classmethod
    def create_provider(
        cls, provider_name: str, config: Optional[Dict[str, Any]] = None
    ) -> EmailProviderInterface:
        """Create a provider instance based on provider name.

        :param provider_name: Name of the provider to create.
        :param config: Optional configuration dictionary.
        :return: Email provider instance.
        :raises ValueError: If provider name is unknown.
        """
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown email provider: {provider_name}")

        logger.info(f"Creating email provider: {provider_name}")
        # All registered providers take config as constructor parameter
        provider_instance = provider_class(config or {})  # type: ignore[call-arg]
        return provider_instance

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names.

        :return: List of available provider names.
        """
        return list(cls._providers.keys())
