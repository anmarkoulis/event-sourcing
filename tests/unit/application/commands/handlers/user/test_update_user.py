"""Unit tests for UpdateUserCommandHandler."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.update_user import (
    UpdateUserCommandHandler,
)
from event_sourcing.application.commands.user.update_user import (
    UpdateUserCommand,
)
from event_sourcing.dto import EventDTO, EventFactory
from event_sourcing.dto.snapshot import UserSnapshotDTO
from event_sourcing.enums import AggregateTypeEnum, HashingMethod


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> UpdateUserCommandHandler:
    return UpdateUserCommandHandler(
        event_store=event_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
        snapshot_store=snapshot_store_mock,
    )


@pytest.fixture
def update_user_command() -> UpdateUserCommand:
    return UpdateUserCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        first_name="New",
        last_name="Name",
        email="new@example.com",
    )


@pytest.fixture
def user_created_event() -> EventDTO:
    """Create a USER_CREATED event for testing."""
    return EventFactory.create_user_created(
        aggregate_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
        hashing_method=HashingMethod.BCRYPT,
        revision=1,
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def user_updated_event() -> EventDTO:
    """Create a USER_UPDATED event for testing."""
    return EventFactory.create_user_updated(
        aggregate_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        first_name="Updated",
        last_name="Name",
        email="updated@example.com",
        revision=2,
        timestamp=datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def user_password_changed_event() -> EventDTO:
    """Create a PASSWORD_CHANGED event for testing."""
    return EventFactory.create_password_changed(
        aggregate_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        password_hash="new_password",  # noqa: S106  # pragma: allowlist secret
        hashing_method=HashingMethod.BCRYPT,
        revision=3,
        timestamp=datetime(2023, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def user_snapshot() -> UserSnapshotDTO:
    """Create a user snapshot for testing."""
    return UserSnapshotDTO(
        aggregate_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        aggregate_type=AggregateTypeEnum.USER,
        data={
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed_password",  # noqa: S106  # pragma: allowlist secret
            "created_at": "2023-01-01T12:00:00+00:00",
            "updated_at": "2023-01-01T12:00:00+00:00",
            "deleted_at": None,
        },
        revision=2,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


class TestUpdateUserCommandHandler:
    """Unit tests for UpdateUserCommandHandler"""

    @pytest.mark.asyncio
    async def test_handle_success_without_snapshot(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
        user_created_event: EventDTO,
    ) -> None:
        """Test successful user update without existing snapshot."""
        # Configure mocks
        event_store_mock.get_stream.return_value = [user_created_event]
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = None

        await handler.handle(update_user_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            update_user_command.user_id,
            AggregateTypeEnum.USER,
            start_revision=None,
        )
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()
        unit_of_work.rollback.assert_not_awaited()

        # Verify snapshot was created
        snapshot_store_mock.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_success_with_snapshot(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
        user_snapshot: UserSnapshotDTO,
        user_password_changed_event: EventDTO,
    ) -> None:
        """Test successful user update with existing snapshot."""
        # Configure mocks
        event_store_mock.get_stream.return_value = [
            user_password_changed_event
        ]
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = user_snapshot

        await handler.handle(update_user_command)

        # Verify event store calls with correct start_revision
        event_store_mock.get_stream.assert_awaited_once_with(
            update_user_command.user_id,
            AggregateTypeEnum.USER,
            start_revision=2,  # From snapshot
        )
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()

        # Verify snapshot was updated
        snapshot_store_mock.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_events_skipped_due_to_revision(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
        user_snapshot: UserSnapshotDTO,
        user_created_event: EventDTO,
        user_updated_event: EventDTO,
        user_password_changed_event: EventDTO,
    ) -> None:
        """Test that events with lower or equal revision are skipped during replay."""
        # Configure mocks
        # Create events with mixed revisions - some should be skipped
        events = [
            user_created_event,  # revision 1 - should be skipped (<= snapshot revision 2)
            user_updated_event,  # revision 2 - should be skipped (== snapshot revision 2)
            user_password_changed_event,  # revision 3 - should be applied (> snapshot revision 2)
        ]
        event_store_mock.get_stream.return_value = events
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = user_snapshot

        await handler.handle(update_user_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            update_user_command.user_id,
            AggregateTypeEnum.USER,
            start_revision=2,
        )
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()

        # Verify snapshot was updated
        snapshot_store_mock.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_no_new_events(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
        user_snapshot: UserSnapshotDTO,
    ) -> None:
        """Test handling when no new events are returned from event store."""
        # Configure mocks - no new events
        event_store_mock.get_stream.return_value = []
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = user_snapshot

        await handler.handle(update_user_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            update_user_command.user_id,
            AggregateTypeEnum.USER,
            start_revision=2,
        )
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()

        # Verify snapshot was updated
        snapshot_store_mock.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_without_snapshot_store(
        self,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
        user_created_event: EventDTO,
    ) -> None:
        """Test handling when no snapshot store is available."""
        # Create handler without snapshot store
        handler = UpdateUserCommandHandler(
            event_store=event_store_mock,
            event_handler=event_handler_mock,
            unit_of_work=unit_of_work,
            snapshot_store=None,
        )

        # Configure mocks
        event_store_mock.get_stream.return_value = [user_created_event]

        await handler.handle(update_user_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            update_user_command.user_id,
            AggregateTypeEnum.USER,
            start_revision=None,
        )
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()
        unit_of_work.commit.assert_awaited_once()

        # Verify no snapshot operations
        # (This would be handled by the handler logic)

    @pytest.mark.asyncio
    async def test_handle_propagates_domain_error(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        update_user_command: UpdateUserCommand,
    ) -> None:
        """Test that domain errors are propagated."""
        # Configure mocks - no events means user doesn't exist
        event_store_mock.get_stream.return_value = []
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = None

        # Now the aggregate will raise UserNotFoundError when no events exist
        from event_sourcing.domain.exceptions import UserNotFoundError

        with pytest.raises(
            UserNotFoundError,
            match="User 11111111-1111-1111-1111-111111111111 not found",
        ):
            await handler.handle(update_user_command)

        # Verify no events were persisted
        event_store_mock.append_to_stream.assert_not_awaited()
        event_handler_mock.dispatch.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_with_snapshot_store_error(
        self,
        handler: UpdateUserCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        update_user_command: UpdateUserCommand,
        user_created_event: EventDTO,
    ) -> None:
        """Test handling when snapshot store operations fail."""
        # Configure mocks
        event_store_mock.get_stream.return_value = [user_created_event]
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = None
        snapshot_store_mock.set.side_effect = Exception("Snapshot store error")

        with pytest.raises(Exception, match="Snapshot store error"):
            await handler.handle(update_user_command)

        # Verify event store operations completed
        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()

        # Verify unit of work was rolled back due to snapshot error
        unit_of_work.rollback.assert_awaited_once()
        unit_of_work.commit.assert_not_awaited()
