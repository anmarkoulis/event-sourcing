"""Unit tests for Celery event handler module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from celery import Celery

from event_sourcing.application.events.handlers.celery import (
    CeleryEventHandler,
)
from event_sourcing.dto import EventDTO
from event_sourcing.enums import EventType, HashingMethod, Role


class TestCeleryEventHandler:
    """Test cases for CeleryEventHandler class."""

    @pytest.fixture
    def mock_celery_app(self) -> MagicMock:
        """Create a mock Celery app."""
        mock_app = MagicMock(spec=Celery)
        mock_app.send_task = MagicMock()
        return mock_app

    @pytest.fixture
    def celery_event_handler(
        self, mock_celery_app: MagicMock
    ) -> CeleryEventHandler:
        """Create a CeleryEventHandler instance with a mock Celery app."""
        return CeleryEventHandler(mock_celery_app)

    @pytest.fixture
    def sample_events(self) -> list[EventDTO]:
        """Create sample events for testing."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()

        return [
            EventDTO(
                id=uuid4(),
                aggregate_id=user_id_1,
                event_type=EventType.USER_CREATED,
                timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
                version="1",
                revision=1,
                data={
                    "username": "testuser",
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                    "password_hash": "hashed_password",  # pragma: allowlist secret
                    "hashing_method": HashingMethod.BCRYPT,
                    "role": Role.USER,
                },
            ),
            EventDTO(
                id=uuid4(),
                aggregate_id=user_id_2,
                event_type=EventType.USER_UPDATED,
                timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
                version="1",
                revision=1,
                data={
                    "first_name": "Updated",
                    "last_name": "User",
                    "email": "updated@example.com",
                },
            ),
        ]

    async def test_dispatch_user_created_event(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching USER_CREATED event through public interface."""
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password_hash": "hashed_password",  # pragma: allowlist secret
                "hashing_method": HashingMethod.BCRYPT,
                "role": Role.USER,
            },
        )

        # Test through public dispatch method
        await celery_event_handler.dispatch([event])

        # Verify both tasks were dispatched
        assert mock_celery_app.send_task.call_count == 2
        mock_celery_app.send_task.assert_any_call(
            "process_user_created_task", args=[event.model_dump()]
        )
        mock_celery_app.send_task.assert_any_call(
            "process_user_created_email_task", args=[event.model_dump()]
        )

    async def test_dispatch_user_updated_event(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching USER_UPDATED event through public interface."""
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={
                "first_name": "Updated",
            },
        )

        # Test through public dispatch method
        await celery_event_handler.dispatch([event])

        # Verify task was dispatched
        mock_celery_app.send_task.assert_called_once_with(
            "process_user_updated_task", args=[event.model_dump()]
        )

    async def test_dispatch_user_deleted_event(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching USER_DELETED event through public interface."""
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={},
        )

        # Test through public dispatch method
        await celery_event_handler.dispatch([event])

        # Verify task was dispatched
        mock_celery_app.send_task.assert_called_once_with(
            "process_user_deleted_task", args=[event.model_dump()]
        )

    async def test_dispatch_password_changed_event(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching PASSWORD_CHANGED event through public interface."""
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={
                "password_hash": "new_hash",  # pragma: allowlist secret
                "hashing_method": HashingMethod.BCRYPT,
            },
        )

        # Test through public dispatch method
        await celery_event_handler.dispatch([event])

        # Verify task was dispatched
        mock_celery_app.send_task.assert_called_once_with(
            "process_password_changed_task", args=[event.model_dump()]
        )

    async def test_dispatch_unknown_event_type(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching event type that has no handler mapping through public interface."""
        # Create a mock event with an invalid event type to test default handler

        mock_event = Mock()
        mock_event.id = uuid4()
        mock_event.aggregate_id = uuid4()
        mock_event.event_type = (
            "INVALID_EVENT_TYPE"  # This will trigger the default case
        )
        mock_event.timestamp = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_event.version = "1"
        mock_event.revision = 1
        mock_event.data = {}
        mock_event.model_dump.return_value = {
            "id": str(mock_event.id),
            "aggregate_id": str(mock_event.aggregate_id),
            "event_type": mock_event.event_type,
            "timestamp": mock_event.timestamp.isoformat(),
            "version": mock_event.version,
            "revision": mock_event.revision,
            "data": mock_event.data,
        }

        # Test through public dispatch method - should handle gracefully and use default handler
        await celery_event_handler.dispatch([mock_event])

        # Verify default task was dispatched
        mock_celery_app.send_task.assert_called_once_with(
            "default_event_handler", args=[mock_event.model_dump()]
        )

    async def test_dispatch_multiple_events(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching multiple events of different types through public interface."""
        events = [
            EventDTO(
                id=uuid4(),
                aggregate_id=uuid4(),
                event_type=EventType.USER_CREATED,
                timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
                version="1",
                revision=1,
                data={"username": "testuser"},
            ),
            EventDTO(
                id=uuid4(),
                aggregate_id=uuid4(),
                event_type=EventType.USER_UPDATED,
                timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
                version="1",
                revision=1,
                data={"first_name": "Updated"},
            ),
        ]

        await celery_event_handler.dispatch(events)

        # Verify total number of tasks sent
        # USER_CREATED: 2 tasks, USER_UPDATED: 1 task = 3 total
        assert mock_celery_app.send_task.call_count == 3

    async def test_dispatch_empty_events_list(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching empty events list through public interface."""
        await celery_event_handler.dispatch([])

        # Verify no tasks were sent
        mock_celery_app.send_task.assert_not_called()

    async def test_dispatch_with_celery_error(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching when Celery raises an error through public interface."""
        mock_celery_app.send_task.side_effect = Exception("Celery error")
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={"username": "testuser"},
        )

        # Verify error is raised
        with pytest.raises(Exception, match="Celery error"):
            await celery_event_handler.dispatch([event])

    async def test_dispatch_with_logging(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test that dispatching logs appropriate messages through public interface."""
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={"username": "testuser"},
        )

        with patch(
            "event_sourcing.application.events.handlers.celery.logger"
        ) as mock_logger:
            await celery_event_handler.dispatch([event])

            # Verify debug logging
            mock_logger.debug.assert_any_call(
                "Dispatching 1 events to Celery tasks"
            )
            mock_logger.debug.assert_any_call(
                "Dispatching event {} to task process_user_created_task".format(
                    event.id
                )
            )
            mock_logger.debug.assert_any_call(
                "Successfully dispatched event {} to task process_user_created_task".format(
                    event.id
                )
            )

    def test_init_with_celery_app(self, mock_celery_app: MagicMock) -> None:
        """Test that CeleryEventHandler is properly initialized with a Celery app."""
        handler = CeleryEventHandler(mock_celery_app)
        assert handler.celery_app == mock_celery_app
