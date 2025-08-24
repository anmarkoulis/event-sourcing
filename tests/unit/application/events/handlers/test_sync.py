"""Unit tests for Sync event handler module."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from event_sourcing.application.events.handlers.sync import SyncEventHandler
from event_sourcing.dto import EventDTO
from event_sourcing.dto.events.user.user_created import (
    UserCreatedDataV1,
    UserCreatedV1,
)
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

    async def test_dispatch_user_created_event(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching USER_CREATED event through public interface."""
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

        # Test through public dispatch method
        await handler.dispatch([event])

        # Verify projections were created and called
        mock_infrastructure_factory.create_user_created_projection.assert_called_once()
        mock_infrastructure_factory.create_user_created_email_projection.assert_called_once()

    async def test_dispatch_user_updated_event(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching USER_UPDATED event through public interface."""
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
            },
        )

        # Test through public dispatch method
        await handler.dispatch([event])

        # Verify projection was created and called
        mock_infrastructure_factory.create_user_updated_projection.assert_called_once()

    async def test_dispatch_user_deleted_event(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching USER_DELETED event through public interface."""
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

        # Test through public dispatch method
        await handler.dispatch([event])

        # Verify projection was created and called
        mock_infrastructure_factory.create_user_deleted_projection.assert_called_once()

    async def test_dispatch_unknown_event_type(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatching event type that has no handler mapping through public interface."""
        handler = SyncEventHandler(mock_infrastructure_factory)
        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,  # Use valid event type but one that has no handler
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={
                "password_hash": "new_hash",  # pragma: allowlist secret
                "hashing_method": HashingMethod.BCRYPT,
            },
        )

        # Test through public dispatch method - should handle gracefully since PASSWORD_CHANGED has no handler
        await handler.dispatch([event])

        # Verify no projections were called for event type with no handler
        mock_infrastructure_factory.create_user_created_projection.assert_not_called()
        mock_infrastructure_factory.create_user_updated_projection.assert_not_called()
        mock_infrastructure_factory.create_user_deleted_projection.assert_not_called()

    async def test_dispatch_with_handler_error(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatch behavior when handler raises an error."""
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

        # Make projection raise an error
        mock_projection = MagicMock()
        mock_projection.handle.side_effect = Exception("Handler error")
        mock_infrastructure_factory.create_user_created_projection.return_value = mock_projection

        # Verify error is raised through public interface
        with pytest.raises(Exception, match="Handler error"):
            await handler.dispatch([event])

    async def test_dispatch_with_multiple_handlers(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatch with multiple handlers for same event type."""
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

        # Test through public dispatch method
        await handler.dispatch([event])

        # Verify both projections were created and called
        mock_infrastructure_factory.create_user_created_projection.assert_called_once()
        mock_infrastructure_factory.create_user_created_email_projection.assert_called_once()

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

    @pytest.mark.asyncio
    async def test_dispatch_without_infrastructure_factory(self) -> None:
        """Test dispatch when no infrastructure factory is available."""
        # Create handler without infrastructure factory
        handler = SyncEventHandler(infrastructure_factory=None)

        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        # This should log warnings but not crash
        await handler.dispatch([event])

        # Verify that the handler processed the event without crashing
        # The warnings will be logged but the event processing continues

    @pytest.mark.asyncio
    async def test_call_handler_without_infrastructure_factory(self) -> None:
        """Test _call_handler when no infrastructure factory is available."""
        # Create handler without infrastructure factory
        handler = SyncEventHandler(infrastructure_factory=None)

        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        # Test each handler type without infrastructure factory
        handlers_to_test = [
            "process_user_created_task",
            "process_user_created_email_task",
            "process_user_updated_task",
            "process_user_deleted_task",
        ]

        for handler_name in handlers_to_test:
            # This should log warnings but not crash
            await handler._call_handler(handler_name, event)

        # Verify that the handler processed all events without crashing
        # The warnings will be logged but the event processing continues

    @pytest.mark.asyncio
    async def test_call_handler_unknown_handler(self) -> None:
        """Test _call_handler with unknown handler name."""
        handler = SyncEventHandler()

        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
                role=Role.USER,
            ),
        )

        # Test with unknown handler
        await handler._call_handler("unknown_handler", event)

        # This should log a warning but not crash

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
        """Test dispatch with logging."""
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

    @pytest.mark.asyncio
    async def test_dispatch_user_updated_without_infrastructure_factory(
        self,
    ) -> None:
        """Test dispatch USER_UPDATED event when no infrastructure factory is available."""
        # Create handler without infrastructure factory
        handler = SyncEventHandler(infrastructure_factory=None)

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

        # This should log warnings but not crash
        await handler.dispatch([event])

        # Verify that the handler processed the event without crashing
        # The warnings will be logged but the event processing continues

    def test_get_handler_functions_unknown_event_type(self) -> None:
        """Test _get_handler_functions with unknown event type."""
        handler = SyncEventHandler()

        # Test with an unknown event type that will trigger the _ case
        # We need to create a mock event type that's not in our enum
        class MockEventType:
            pass

        mock_event_type = MockEventType()

        # This should return the default handler
        result = handler._get_handler_functions(mock_event_type)
        assert result == ["default_event_handler"]

    async def test_call_handler_unknown_handler_case(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test _call_handler with unknown handler name to cover the _ case."""
        handler = SyncEventHandler(mock_infrastructure_factory)

        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={"username": "testuser"},
        )

        # Test with unknown handler to trigger the _ case
        await handler._call_handler("unknown_handler", event)

        # This should log a warning but not crash
        # The method should complete without raising an exception

    async def test_dispatch_with_unknown_handler(
        self, mock_infrastructure_factory: MagicMock
    ) -> None:
        """Test dispatch with unknown handler to cover the _ case in _call_handler."""
        handler = SyncEventHandler(mock_infrastructure_factory)

        event = EventDTO(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data={"username": "testuser"},
        )

        # Mock _get_handler_functions to return an unknown handler
        with patch.object(
            handler, "_get_handler_functions", return_value=["unknown_handler"]
        ):
            # This should trigger the _ case in _call_handler
            await handler.dispatch([event])

        # The handler should log a warning but not crash
        # The method should complete without raising an exception
