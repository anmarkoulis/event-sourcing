"""Unit tests for Sync event handler module."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from event_sourcing.application.events.handlers.sync import SyncEventHandler
from event_sourcing.dto import EventDTO
from event_sourcing.enums import EventType, HashingMethod, Role


class TestSyncEventHandler:
    """Test cases for SyncEventHandler class."""

    @pytest.fixture
    def mock_infrastructure_factory(self) -> MagicMock:
        """Create a mock infrastructure factory."""
        factory = MagicMock()
        factory.create_user_created_projection = MagicMock(
            return_value=MagicMock(handle=AsyncMock())
        )
        factory.create_user_created_email_projection = MagicMock(
            return_value=MagicMock(handle=AsyncMock())
        )
        factory.create_user_updated_projection = MagicMock(
            return_value=MagicMock(handle=AsyncMock())
        )
        factory.create_user_deleted_projection = MagicMock(
            return_value=MagicMock(handle=AsyncMock())
        )
        return factory

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

    def test_init_with_infrastructure_factory(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test initialization with infrastructure factory."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        assert handler.infrastructure_factory == mock_infrastructure_factory

    def test_init_without_infrastructure_factory(self) -> None:
        """Test initialization without infrastructure factory."""
        handler = SyncEventHandler()
        assert handler.infrastructure_factory is None

    async def test_dispatch_user_created_events(
        self,
        mock_infrastructure_factory: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching USER_CREATED events."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        user_created_event = sample_events[0]

        await handler.dispatch([user_created_event])

        # Verify both projections were called
        mock_infrastructure_factory.create_user_created_projection.assert_called_once()
        mock_infrastructure_factory.create_user_created_email_projection.assert_called_once()

    async def test_dispatch_user_updated_events(
        self,
        mock_infrastructure_factory: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching USER_UPDATED events."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        user_updated_event = sample_events[1]

        await handler.dispatch([user_updated_event])

        # Verify projection was called
        mock_infrastructure_factory.create_user_updated_projection.assert_called_once()

    async def test_dispatch_user_deleted_events(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching USER_DELETED events."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        user_deleted_event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={},
        )

        await handler.dispatch([user_deleted_event])

        # Verify projection was called
        mock_infrastructure_factory.create_user_deleted_projection.assert_called_once()

    async def test_dispatch_password_changed_events(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching PASSWORD_CHANGED events."""
        handler = SyncEventHandler(mock_infrastructure_factory)
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

        await handler.dispatch([password_changed_event])

        # Verify no projections were called (PASSWORD_CHANGED not handled in sync mode)
        mock_infrastructure_factory.create_user_created_projection.assert_not_called()
        mock_infrastructure_factory.create_user_updated_projection.assert_not_called()
        mock_infrastructure_factory.create_user_deleted_projection.assert_not_called()

    async def test_dispatch_multiple_events(
        self,
        mock_infrastructure_factory: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching multiple events of different types."""
        handler = SyncEventHandler(mock_infrastructure_factory)

        await handler.dispatch(sample_events)

        # Verify projections were called for each event type
        mock_infrastructure_factory.create_user_created_projection.assert_called_once()
        mock_infrastructure_factory.create_user_updated_projection.assert_called_once()

    async def test_dispatch_empty_events_list(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching empty events list."""
        handler = SyncEventHandler(mock_infrastructure_factory)

        await handler.dispatch([])

        # Verify no projections were called
        mock_infrastructure_factory.create_user_created_projection.assert_not_called()
        mock_infrastructure_factory.create_user_updated_projection.assert_not_called()
        mock_infrastructure_factory.create_user_deleted_projection.assert_not_called()

    async def test_dispatch_without_infrastructure_factory(
        self, sample_events: list[EventDTO]
    ) -> None:
        """Test dispatching without infrastructure factory."""
        handler = SyncEventHandler()

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            await handler.dispatch([sample_events[0]])

            # Verify warning was logged
            mock_logger.warning.assert_any_call(
                "No infrastructure factory available for user created projection"
            )

    async def test_dispatch_with_projection_error(
        self,
        mock_infrastructure_factory: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test dispatching when projection raises an error."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        user_created_event = sample_events[0]

        # Make projection raise an error
        mock_projection = MagicMock()
        mock_projection.handle.side_effect = Exception("Projection error")
        mock_infrastructure_factory.create_user_created_projection.return_value = mock_projection

        # Verify error is raised
        with pytest.raises(Exception, match="Projection error"):
            await handler.dispatch([user_created_event])

    async def test_dispatch_with_logging(
        self,
        mock_infrastructure_factory: MagicMock,
        sample_events: list[EventDTO],
    ) -> None:
        """Test that dispatching logs appropriate messages."""
        handler = SyncEventHandler(mock_infrastructure_factory)

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            await handler.dispatch([sample_events[0]])

            # Verify debug logging
            mock_logger.debug.assert_any_call(
                "Processing 1 events synchronously"
            )
            mock_logger.debug.assert_any_call(
                "Processing event {} with handler process_user_created_task".format(
                    sample_events[0].id
                )
            )
            mock_logger.debug.assert_any_call(
                "Successfully processed event {} with handler process_user_created_task".format(
                    sample_events[0].id
                )
            )

    def test_get_handler_functions_user_created(self) -> None:
        """Test getting handler functions for USER_CREATED event type."""
        handler = SyncEventHandler()
        handler_functions = handler._get_handler_functions(
            EventType.USER_CREATED
        )

        expected_handlers = [
            "process_user_created_task",
            "process_user_created_email_task",
        ]
        assert handler_functions == expected_handlers

    def test_get_handler_functions_user_updated(self) -> None:
        """Test getting handler functions for USER_UPDATED event type."""
        handler = SyncEventHandler()
        handler_functions = handler._get_handler_functions(
            EventType.USER_UPDATED
        )

        expected_handlers = ["process_user_updated_task"]
        assert handler_functions == expected_handlers

    def test_get_handler_functions_user_deleted(self) -> None:
        """Test getting handler functions for USER_DELETED event type."""
        handler = SyncEventHandler()
        handler_functions = handler._get_handler_functions(
            EventType.USER_DELETED
        )

        expected_handlers = ["process_user_deleted_task"]
        assert handler_functions == expected_handlers

    def test_get_handler_functions_unknown_event_type(self) -> None:
        """Test getting handler functions for unknown event type."""
        handler = SyncEventHandler()
        handler_functions = handler._get_handler_functions("UNKNOWN_EVENT")

        expected_handlers = ["default_event_handler"]
        assert handler_functions == expected_handlers

    async def test_call_handler_user_created_task(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling user created task handler."""
        handler = SyncEventHandler(mock_infrastructure_factory)
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

        await handler._call_handler("process_user_created_task", event)

        # Verify projection was created and called
        mock_infrastructure_factory.create_user_created_projection.assert_called_once()

    async def test_call_handler_user_created_email_task(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling user created email task handler."""
        handler = SyncEventHandler(mock_infrastructure_factory)
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

        await handler._call_handler("process_user_created_email_task", event)

        # Verify projection was created and called
        mock_infrastructure_factory.create_user_created_email_projection.assert_called_once()

    async def test_call_handler_user_updated_task(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling user updated task handler."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={
                "first_name": "Updated",
                "last_name": "User",
                "email": "updated@example.com",
            },
        )

        await handler._call_handler("process_user_updated_task", event)

        # Verify projection was created and called
        mock_infrastructure_factory.create_user_updated_projection.assert_called_once()

    async def test_call_handler_user_deleted_task(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling user deleted task handler."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={},
        )

        await handler._call_handler("process_user_deleted_task", event)

        # Verify projection was created and called
        mock_infrastructure_factory.create_user_deleted_projection.assert_called_once()

    async def test_call_handler_unknown_handler(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling unknown handler."""
        handler = SyncEventHandler(mock_infrastructure_factory)
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

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            await handler._call_handler("unknown_handler", event)

            # Verify warning was logged
            mock_logger.warning.assert_called_once_with(
                "Unknown handler: unknown_handler"
            )

    async def test_call_handler_without_infrastructure_factory(self) -> None:
        """Test calling handler without infrastructure factory."""
        handler = SyncEventHandler()
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

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            await handler._call_handler("process_user_created_task", event)

            # Verify warning was logged
            mock_logger.warning.assert_any_call(
                "No infrastructure factory available for user created projection"
            )

    async def test_call_handler_with_import_error(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling handler when ImportError occurs."""
        handler = SyncEventHandler(mock_infrastructure_factory)
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

        # Make the infrastructure factory method raise an ImportError
        mock_infrastructure_factory.create_user_created_projection.side_effect = ImportError(
            "Module not found"
        )

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            with pytest.raises(ImportError, match="Module not found"):
                await handler._call_handler("process_user_created_task", event)

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "Could not import handler process_user_created_task: Module not found"
            )

    async def test_call_handler_with_general_exception(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test calling handler when a general Exception occurs."""
        handler = SyncEventHandler(mock_infrastructure_factory)
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

        # Make the infrastructure factory method raise a general Exception
        mock_infrastructure_factory.create_user_created_projection.side_effect = Exception(
            "General error"
        )

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            with pytest.raises(Exception, match="General error"):
                await handler._call_handler("process_user_created_task", event)

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "Error calling handler process_user_created_task: General error"
            )

    async def test_call_handler_user_updated_without_factory(self) -> None:
        """Test calling user updated handler without infrastructure factory."""
        handler = SyncEventHandler()
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={
                "first_name": "Updated",
                "last_name": "User",
                "email": "updated@example.com",
            },
        )

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            await handler._call_handler("process_user_updated_task", event)

            # Verify warning was logged
            mock_logger.warning.assert_called_once_with(
                "No infrastructure factory available for user updated projection"
            )

    async def test_call_handler_user_deleted_without_factory(self) -> None:
        """Test calling user deleted handler without infrastructure factory."""
        handler = SyncEventHandler()
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={},
        )

        with patch(
            "event_sourcing.application.events.handlers.sync.logger"
        ) as mock_logger:
            await handler._call_handler("process_user_deleted_task", event)

            # Verify warning was logged
            mock_logger.warning.assert_called_once_with(
                "No infrastructure factory available for user deleted projection"
            )
