import logging
from typing import Any, Dict, Type

from .provider_interface import CRMProviderInterface

logger = logging.getLogger(__name__)


class CRMProviderFactory:
    """Factory for creating CRM providers"""

    _providers: Dict[str, Type[CRMProviderInterface]] = {}

    @classmethod
    def register_provider(
        cls, provider_name: str, provider_class: type
    ) -> None:
        """Register a provider class with the factory"""
        cls._providers[provider_name.lower()] = provider_class
        logger.info(f"Registered CRM provider: {provider_name}")

    @classmethod
    def create_provider(
        cls, provider_name: str, config: Dict[str, Any]
    ) -> CRMProviderInterface:
        """Create a provider instance based on provider name"""
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown CRM provider: {provider_name}")

        logger.info(f"Creating CRM provider: {provider_name}")
        # All registered providers take config as constructor parameter
        provider_instance: CRMProviderInterface = provider_class(config)  # type: ignore
        return provider_instance

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names"""
        return list(cls._providers.keys())
