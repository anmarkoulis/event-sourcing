"""Unit tests for user_updated_task.

These tests verify that the task calls the proper projection without
testing the full infrastructure.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from event_sourcing.application.tasks.user.user_updated import (
    process_user_updated_task,
)
from event_sourcing.dto.events.factory import EventFactory


class TestUserUpdatedTask:
    """Test the user_updated_task Celery task."""

    @patch(
        "event_sourcing.application.tasks.user.user_updated.get_infrastructure_factory"
    )
    def test_process_user_updated_task_executes_without_exception(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_updated_task executes without raising exceptions."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_updated_projection.return_value = (
            mock_projection
        )

        # Create a test event using the factory
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            username="newusername",
            email="newemail@example.com",
            first_name="NewFirstName",
            last_name="NewLastName",
            timestamp=datetime.now(timezone.utc),
        )

        # Convert the event to a dictionary format that the task expects
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_updated_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_updated.get_infrastructure_factory"
    )
    def test_process_user_updated_task_with_username_only(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_updated_task works with only username update."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_updated_projection.return_value = (
            mock_projection
        )

        # Create a test event with only username update
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            username="newusername",
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_updated_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_updated.get_infrastructure_factory"
    )
    def test_process_user_updated_task_with_email_only(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_updated_task works with only email update."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_updated_projection.return_value = (
            mock_projection
        )

        # Create a test event with only email update
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            email="newemail@example.com",
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_updated_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_updated.get_infrastructure_factory"
    )
    def test_process_user_updated_task_with_name_only(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_updated_task works with only name updates."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_updated_projection.return_value = (
            mock_projection
        )

        # Create a test event with only first name update
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            first_name="NewFirstName",
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_updated_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

        # Create a test event with only last name update
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            last_name="NewLastName",
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_projection.handle.assert_called()

    @patch(
        "event_sourcing.application.tasks.user.user_updated.get_infrastructure_factory"
    )
    def test_process_user_updated_task_with_partial_updates(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_updated_task works with partial field updates."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_updated_projection.return_value = (
            mock_projection
        )

        # Create a test event with partial updates
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            username="partialuser",
            email="partial@example.com",
            # first_name and last_name are None (not updated)
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_updated_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_updated.get_infrastructure_factory"
    )
    def test_process_user_updated_task_with_all_fields(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_updated_task works with all fields updated."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_updated_projection.return_value = (
            mock_projection
        )

        # Create a test event with all fields updated
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_updated(
            aggregate_id=test_user_id,
            username="allfieldsuser",
            email="allfields@example.com",
            first_name="AllFields",
            last_name="User",
            timestamp=datetime.now(timezone.utc),
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_updated_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_updated_projection.assert_called_once()
        mock_projection.handle.assert_called_once()
