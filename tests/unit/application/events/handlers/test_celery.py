"""Unit tests for Celery event handler module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
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

    async def test_dispatch_user_created_events(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching USER_CREATED events."""
        user_created_event = sample_events[0]

        await celery_event_handler.dispatch([user_created_event])

        # Verify Celery tasks were sent
        assert mock_celery_app.send_task.call_count == 2

        # Check first call (process_user_created_task)
        first_call = mock_celery_app.send_task.call_args_list[0]
        assert first_call.args[0] == "process_user_created_task"
        assert first_call.kwargs["args"] == [user_created_event.model_dump()]

        # Check second call (process_user_created_email_task)
        second_call = mock_celery_app.send_task.call_args_list[1]
        assert second_call.args[0] == "process_user_created_email_task"
        assert second_call.kwargs["args"] == [user_created_event.model_dump()]

    async def test_dispatch_user_updated_events(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching USER_UPDATED events."""
        user_updated_event = sample_events[1]

        await celery_event_handler.dispatch([user_updated_event])

        # Verify Celery task was sent
        mock_celery_app.send_task.assert_called_once_with(
            "process_user_updated_task", args=[user_updated_event.model_dump()]
        )

    async def test_dispatch_user_deleted_events(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching USER_DELETED events."""
        user_deleted_event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={},
        )

        await celery_event_handler.dispatch([user_deleted_event])

        # Verify Celery task was sent
        mock_celery_app.send_task.assert_called_once_with(
            "process_user_deleted_task", args=[user_deleted_event.model_dump()]
        )

    async def test_dispatch_password_changed_events(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching PASSWORD_CHANGED events."""
        password_changed_event = EventDTO(
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

        await celery_event_handler.dispatch([password_changed_event])

        # Verify Celery task was sent
        mock_celery_app.send_task.assert_called_once_with(
            "process_password_changed_task",
            args=[password_changed_event.model_dump()],
        )

    async def test_dispatch_multiple_events(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching multiple events of different types."""
        await celery_event_handler.dispatch(sample_events)

        # Verify total number of tasks sent
        # USER_CREATED: 2 tasks, USER_UPDATED: 1 task = 3 total
        assert mock_celery_app.send_task.call_count == 3

    async def test_dispatch_empty_events_list(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
    ) -> None:
        """Test dispatching empty events list."""
        await celery_event_handler.dispatch([])

        # Verify no tasks were sent
        mock_celery_app.send_task.assert_not_called()

    async def test_dispatch_with_celery_error(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching when Celery raises an error."""
        mock_celery_app.send_task.side_effect = Exception("Celery error")

        # Verify error is raised
        with pytest.raises(Exception, match="Celery error"):
            await celery_event_handler.dispatch([sample_events[0]])

    async def test_dispatch_with_logging(
        self,
        celery_event_handler: CeleryEventHandler,
        mock_celery_app: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test that dispatching logs appropriate messages."""
        with patch(
            "event_sourcing.application.events.handlers.celery.logger"
        ) as mock_logger:
            await celery_event_handler.dispatch([sample_events[0]])

            # Verify debug logging
            mock_logger.debug.assert_any_call(
                "Dispatching 1 events to Celery tasks"
            )
            mock_logger.debug.assert_any_call(
                "Dispatching event {} to task process_user_created_task".format(
                    sample_events[0].id
                )
            )
            mock_logger.debug.assert_any_call(
                "Successfully dispatched event {} to task process_user_created_task".format(
                    sample_events[0].id
                )
            )

    def test_init_with_celery_app(self, mock_celery_app: MagicMock) -> None:
        """Test that CeleryEventHandler is properly initialized with a Celery app."""
        handler = CeleryEventHandler(mock_celery_app)
        assert handler.celery_app == mock_celery_app

    def test_get_task_names_user_created(
        self, celery_event_handler: CeleryEventHandler
    ) -> None:
        """Test getting task names for USER_CREATED event type."""
        task_names = celery_event_handler._get_task_names(
            EventType.USER_CREATED
        )

        expected_tasks = [
            "process_user_created_task",
            "process_user_created_email_task",
        ]
        assert task_names == expected_tasks

    def test_get_task_names_user_updated(
        self, celery_event_handler: CeleryEventHandler
    ) -> None:
        """Test getting task names for USER_UPDATED event type."""
        task_names = celery_event_handler._get_task_names(
            EventType.USER_UPDATED
        )

        expected_tasks = ["process_user_updated_task"]
        assert task_names == expected_tasks

    def test_get_task_names_user_deleted(
        self, celery_event_handler: CeleryEventHandler
    ) -> None:
        """Test getting task names for USER_DELETED event type."""
        task_names = celery_event_handler._get_task_names(
            EventType.USER_DELETED
        )

        expected_tasks = ["process_user_deleted_task"]
        assert task_names == expected_tasks

    def test_get_task_names_password_changed(
        self, celery_event_handler: CeleryEventHandler
    ) -> None:
        """Test getting task names for PASSWORD_CHANGED event type."""
        task_names = celery_event_handler._get_task_names(
            EventType.PASSWORD_CHANGED
        )

        expected_tasks = ["process_password_changed_task"]
        assert task_names == expected_tasks

    def test_get_task_names_unknown_event_type(
        self, celery_event_handler: CeleryEventHandler
    ) -> None:
        """Test getting task names for unknown event type."""
        task_names = celery_event_handler._get_task_names("UNKNOWN_EVENT")

        expected_tasks = ["default_event_handler"]
        assert task_names == expected_tasks
