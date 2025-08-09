from unittest.mock import AsyncMock, MagicMock

import pytest

from event_sourcing.application.projections.user.user_created_email import (
    UserCreatedEmailProjection,
)
from event_sourcing.dto.events.factory import EventFactory
from event_sourcing.infrastructure.providers.email import (
    EmailProviderInterface,
)


class TestUserCreatedEmailProjection:
    """Test cases for UserCreatedEmailProjection"""

    @pytest.fixture
    def email_provider(self) -> MagicMock:
        """Create a mock email provider"""
        provider = MagicMock(spec=EmailProviderInterface)
        provider.send_email = AsyncMock(return_value=True)
        provider.get_provider_name.return_value = "logging"
        provider.is_available.return_value = True
        return provider

    @pytest.fixture
    def projection(
        self, email_provider: MagicMock
    ) -> UserCreatedEmailProjection:
        """Create a UserCreatedEmailProjection instance"""
        return UserCreatedEmailProjection(email_provider=email_provider)

    @pytest.fixture
    def user_created_event(self) -> EventFactory:
        """Create a sample USER_CREATED event"""
        return EventFactory.create_user_created(
            aggregate_id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",  # pragma: allowlist secret  # noqa: S106
            revision=1,
        )

    @pytest.mark.asyncio
    async def test_handle_user_created_event_sends_email(
        self,
        projection: UserCreatedEmailProjection,
        user_created_event: EventFactory,
        email_provider: MagicMock,
    ) -> None:
        """Test that handling a USER_CREATED event sends a welcome email"""
        # Act
        await projection.handle(user_created_event)

        # Assert
        email_provider.send_email.assert_called_once()
        call_args = email_provider.send_email.call_args

        # Check email parameters
        assert call_args.kwargs["to_email"] == "test@example.com"
        assert call_args.kwargs["subject"] == "Welcome to Our Platform!"
        assert call_args.kwargs["from_email"] == "welcome@example.com"
        assert "Welcome to our platform!" in call_args.kwargs["body"]
        assert "testuser" in call_args.kwargs["body"]

    @pytest.mark.asyncio
    async def test_handle_user_created_event_with_minimal_data(
        self, projection: UserCreatedEmailProjection, email_provider: MagicMock
    ) -> None:
        """Test that handling a USER_CREATED event with minimal data works"""
        # Arrange
        event = EventFactory.create_user_created(
            aggregate_id="123e4567-e89b-12d3-a456-426614174001",
            username="minimaluser",
            email="minimal@example.com",
            first_name="",
            last_name="",
            password_hash="hashed_password",  # pragma: allowlist secret  # noqa: S106
            revision=1,
        )

        # Act
        await projection.handle(event)

        # Assert
        email_provider.send_email.assert_called_once()
        call_args = email_provider.send_email.call_args
        assert call_args.kwargs["to_email"] == "minimal@example.com"
        assert "minimaluser" in call_args.kwargs["body"]

    @pytest.mark.asyncio
    async def test_handle_user_created_event_email_failure(
        self,
        projection: UserCreatedEmailProjection,
        user_created_event: EventFactory,
        email_provider: MagicMock,
    ) -> None:
        """Test that email failure is handled gracefully"""
        # Arrange
        email_provider.send_email.return_value = False

        # Act & Assert
        with pytest.raises(Exception):
            await projection.handle(user_created_event)

    def test_create_welcome_email_body(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test the welcome email body creation"""
        # Act
        body = projection._create_welcome_email_body(
            first_name="John",
            last_name="Doe",
            username="johndoe",
        )

        # Assert
        assert "Dear John Doe," in body
        assert "johndoe" in body
        assert "Welcome to our platform!" in body
        assert "Your account has been successfully created" in body

    def test_create_welcome_email_body_with_empty_names(
        self, projection: UserCreatedEmailProjection
    ) -> None:
        """Test the welcome email body creation with empty names"""
        # Act
        body = projection._create_welcome_email_body(
            first_name="",
            last_name="",
            username="testuser",
        )

        # Assert
        assert (
            "Dear testuser," in body
        )  # Should use username when names are empty
        assert "testuser" in body
