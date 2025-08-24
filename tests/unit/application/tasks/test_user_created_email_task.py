"""Unit tests for user_created_email_task.

These tests verify that the task calls the proper projection without
testing the full infrastructure.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from event_sourcing.application.tasks.user.user_created_email import (
    process_user_created_email_task,
)
from event_sourcing.dto.events.factory import EventFactory
from event_sourcing.enums import HashingMethod, Role


class TestUserCreatedEmailTask:
    """Test the user_created_email_task Celery task."""

    @patch(
        "event_sourcing.application.tasks.user.user_created_email.get_infrastructure_factory"
    )
    def test_process_user_created_email_task_executes_without_exception(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_created_email_task executes without raising exceptions."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_created_email_projection.return_value = (
            mock_projection
        )

        # Create a test event using the factory
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_created(
            aggregate_id=test_user_id,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password_123",  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            role=Role.USER,
            timestamp=datetime.now(timezone.utc),
        )

        # Convert the event to a dictionary format that the task expects
        event_dict = test_event.model_dump()

        # Act
        result = process_user_created_email_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_created_email_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_created_email.get_infrastructure_factory"
    )
    def test_process_user_created_email_task_with_minimal_data(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_created_email_task works with minimal event data."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_created_email_projection.return_value = (
            mock_projection
        )

        # Create a test event with minimal data
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_created(
            aggregate_id=test_user_id,
            username="minimaluser",
            email="minimal@example.com",
            first_name="Minimal",
            last_name="User",
            password_hash="minimal_hash",  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_created_email_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_created_email_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_created_email.get_infrastructure_factory"
    )
    def test_process_user_created_email_task_with_admin_role(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_created_email_task works with admin role."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_created_email_projection.return_value = (
            mock_projection
        )

        # Create a test event with admin role
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_created(
            aggregate_id=test_user_id,
            username="adminuser",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password_hash="admin_hash",  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            role=Role.ADMIN,
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_created_email_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_created_email_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_created_email.get_infrastructure_factory"
    )
    def test_process_user_created_email_task_with_different_email_formats(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_created_email_task works with different email formats."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_created_email_projection.return_value = (
            mock_projection
        )

        # Test with different email formats
        test_cases = [
            "simple@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
        ]

        for email in test_cases:
            test_user_id = uuid.uuid4()
            test_event = EventFactory.create_user_created(
                aggregate_id=test_user_id,
                username=f"user_{email.split('@')[0]}",
                email=email,
                first_name="Email",
                last_name="Test",
                password_hash="email_test_hash",  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            )

            # Convert the event to a dictionary format
            event_dict = test_event.model_dump()

            # Act
            result = process_user_created_email_task(event_dict)

            # Assert
            assert result is None
            mock_projection.handle.assert_called()

        # Verify the projection was created and called for each test case
        assert (
            mock_factory.create_user_created_email_projection.call_count
            == len(test_cases)
        )
        assert mock_projection.handle.call_count == len(test_cases)
