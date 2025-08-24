"""Unit tests for user_deleted_task.

These tests verify that the task calls the proper projection without
testing the full infrastructure.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from event_sourcing.application.tasks.user.user_deleted import (
    process_user_deleted_task,
)
from event_sourcing.dto.events.factory import EventFactory


class TestUserDeletedTask:
    """Test the user_deleted_task Celery task."""

    @patch(
        "event_sourcing.application.tasks.user.user_deleted.get_infrastructure_factory"
    )
    def test_process_user_deleted_task_executes_without_exception(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_deleted_task executes without raising exceptions."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_deleted_projection.return_value = (
            mock_projection
        )

        # Create a test event using the factory
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_deleted(
            aggregate_id=test_user_id,
            revision=1,
            timestamp=datetime.now(timezone.utc),
        )

        # Convert the event to a dictionary format that the task expects
        event_dict = test_event.model_dump()

        # Act
        result = process_user_deleted_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_deleted_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_deleted.get_infrastructure_factory"
    )
    def test_process_user_deleted_task_with_minimal_data(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_deleted_task works with minimal event data."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_deleted_projection.return_value = (
            mock_projection
        )

        # Create a test event with minimal data
        test_user_id = uuid.uuid4()
        test_event = EventFactory.create_user_deleted(
            aggregate_id=test_user_id,
            revision=1,
        )

        # Convert the event to a dictionary format
        event_dict = test_event.model_dump()

        # Act
        result = process_user_deleted_task(event_dict)

        # Assert
        assert result is None
        mock_factory.create_user_deleted_projection.assert_called_once()
        mock_projection.handle.assert_called_once()

    @patch(
        "event_sourcing.application.tasks.user.user_deleted.get_infrastructure_factory"
    )
    def test_process_user_deleted_task_with_different_revisions(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_deleted_task works with different revision numbers."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_deleted_projection.return_value = (
            mock_projection
        )

        # Test with different revision numbers
        test_revisions = [1, 2, 5, 10, 100]

        for revision in test_revisions:
            test_user_id = uuid.uuid4()
            test_event = EventFactory.create_user_deleted(
                aggregate_id=test_user_id,
                revision=revision,
            )

            # Convert the event to a dictionary format
            event_dict = test_event.model_dump()

            # Act
            result = process_user_deleted_task(event_dict)

            # Assert
            assert result is None
            mock_projection.handle.assert_called()

        # Verify the projection was created and called for each test case
        assert mock_factory.create_user_deleted_projection.call_count == len(
            test_revisions
        )
        assert mock_projection.handle.call_count == len(test_revisions)

    @patch(
        "event_sourcing.application.tasks.user.user_deleted.get_infrastructure_factory"
    )
    def test_process_user_deleted_task_with_different_timestamps(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_deleted_task works with different timestamps."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_deleted_projection.return_value = (
            mock_projection
        )

        # Test with different timestamps
        test_timestamps = [
            datetime.now(timezone.utc),
            datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2023, 6, 15, 18, 30, 0, tzinfo=timezone.utc),
            datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        ]

        for timestamp in test_timestamps:
            test_user_id = uuid.uuid4()
            test_event = EventFactory.create_user_deleted(
                aggregate_id=test_user_id,
                revision=1,
                timestamp=timestamp,
            )

            # Convert the event to a dictionary format
            event_dict = test_event.model_dump()

            # Act
            result = process_user_deleted_task(event_dict)

            # Assert
            assert result is None
            mock_projection.handle.assert_called()

        # Verify the projection was created and called for each test case
        assert mock_factory.create_user_deleted_projection.call_count == len(
            test_timestamps
        )
        assert mock_projection.handle.call_count == len(test_timestamps)

    @patch(
        "event_sourcing.application.tasks.user.user_deleted.get_infrastructure_factory"
    )
    def test_process_user_deleted_task_with_high_revision_numbers(
        self, mock_get_infrastructure_factory: Mock
    ) -> None:
        """Test that process_user_deleted_task works with high revision numbers."""
        # Arrange
        mock_factory = Mock()
        mock_get_infrastructure_factory.return_value = mock_factory

        mock_projection = Mock()
        mock_projection.handle = AsyncMock()
        mock_factory.create_user_deleted_projection.return_value = (
            mock_projection
        )

        # Test with high revision numbers that might occur in long-running systems
        test_revisions = [1000, 10000, 100000]

        for revision in test_revisions:
            test_user_id = uuid.uuid4()
            test_event = EventFactory.create_user_deleted(
                aggregate_id=test_user_id,
                revision=revision,
            )

            # Convert the event to a dictionary format
            event_dict = test_event.model_dump()

            # Act
            result = process_user_deleted_task(event_dict)

            # Assert
            assert result is None
            mock_projection.handle.assert_called()

        # Verify the projection was created and called for each test case
        assert mock_factory.create_user_deleted_projection.call_count == len(
            test_revisions
        )
        assert mock_projection.handle.call_count == len(test_revisions)
