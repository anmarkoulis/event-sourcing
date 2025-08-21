from unittest.mock import MagicMock

import pytest

from event_sourcing.infrastructure.providers.email import (
    EmailProviderFactory,
    LoggingEmailProvider,
)


class TestEmailProviderFactory:
    """Test cases for EmailProviderFactory"""

    def setup_method(self) -> None:
        """Reset the factory before each test"""
        EmailProviderFactory._providers.clear()

    def test_register_provider(self) -> None:
        """Test that register_provider adds a provider to the factory"""
        # Act
        EmailProviderFactory.register_provider("test", LoggingEmailProvider)

        # Assert
        assert "test" in EmailProviderFactory._providers
        assert EmailProviderFactory._providers["test"] == LoggingEmailProvider

    def test_create_provider_success(self) -> None:
        """Test that create_provider creates a provider instance"""
        # Arrange
        EmailProviderFactory.register_provider("logging", LoggingEmailProvider)

        # Act
        provider = EmailProviderFactory.create_provider("logging")

        # Assert
        assert isinstance(provider, LoggingEmailProvider)
        assert provider.get_provider_name() == "logging"

    def test_create_provider_with_config(self) -> None:
        """Test that create_provider passes config to provider"""
        # Arrange
        EmailProviderFactory.register_provider("logging", LoggingEmailProvider)
        config = {"default_from_email": "custom@example.com"}

        # Act
        provider = EmailProviderFactory.create_provider("logging", config)

        # Assert
        assert (
            provider.get_config()["default_from_email"] == "custom@example.com"
        )

    def test_create_provider_unknown_provider(self) -> None:
        """Test that create_provider raises error for unknown provider"""
        # Act & Assert
        from event_sourcing.exceptions import UnknownProviderError

        with pytest.raises(
            UnknownProviderError, match="Unknown email: unknown"
        ):
            EmailProviderFactory.create_provider("unknown")

    def test_create_provider_case_insensitive(self) -> None:
        """Test that create_provider is case insensitive"""
        # Arrange
        EmailProviderFactory.register_provider("Logging", LoggingEmailProvider)

        # Act
        provider = EmailProviderFactory.create_provider("logging")

        # Assert
        assert isinstance(provider, LoggingEmailProvider)

    def test_get_available_providers(self) -> None:
        """Test that get_available_providers returns list of provider names"""
        # Arrange
        EmailProviderFactory.register_provider("logging", LoggingEmailProvider)
        EmailProviderFactory.register_provider("smtp", MagicMock())

        # Act
        providers = EmailProviderFactory.get_available_providers()

        # Assert
        assert "logging" in providers
        assert "smtp" in providers
        assert len(providers) == 2

    def test_get_available_providers_empty(self) -> None:
        """Test that get_available_providers returns empty list when no providers"""
        # Act
        providers = EmailProviderFactory.get_available_providers()

        # Assert
        assert providers == []
