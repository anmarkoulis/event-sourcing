"""Unit tests for infrastructure provider module."""

from unittest.mock import MagicMock, patch

from event_sourcing.infrastructure.provider import (
    InfrastructureFactoryDep,
    get_infrastructure_factory,
)


class TestProvider:
    """Test cases for provider module."""

    @patch("event_sourcing.infrastructure.provider.settings")
    @patch("event_sourcing.infrastructure.provider.InfrastructureFactory")
    def test_get_infrastructure_factory(
        self, mock_factory_class: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test get_infrastructure_factory function."""
        # Arrange
        mock_settings.DATABASE_URL = (
            "postgresql://test:test@localhost/test"  # pragma: allowlist secret
        )
        mock_factory_instance = MagicMock()
        mock_factory_class.return_value = mock_factory_instance

        # Act
        result = get_infrastructure_factory()

        # Assert
        mock_factory_class.assert_called_once_with(
            database_url="postgresql://test:test@localhost/test"  # pragma: allowlist secret
        )
        assert result == mock_factory_instance

    def test_infrastructure_factory_dep_type_alias(self) -> None:
        """Test that InfrastructureFactoryDep type alias is properly defined."""
        # This test ensures the type alias is imported and accessible
        # The actual functionality is tested through FastAPI dependency injection
        assert InfrastructureFactoryDep is not None

        # Verify it's a type annotation (this is a basic check)
        # In practice, this would be used in FastAPI route parameters
        type_str = str(InfrastructureFactoryDep)
        assert "Annotated" in type_str
        assert "InfrastructureFactory" in type_str
        assert "Depends" in type_str
