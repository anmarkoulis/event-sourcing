"""Unit tests for ChangePasswordCommandHandler."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from event_sourcing.application.commands.handlers.user.change_password import (
    ChangePasswordCommandHandler,
)
from event_sourcing.application.commands.user.change_password import (
    ChangePasswordCommand,
)
from event_sourcing.dto import EventDTO, EventFactory
from event_sourcing.dto.snapshot import UserSnapshotDTO
from event_sourcing.enums import AggregateTypeEnum


@pytest.fixture
def handler(
    event_store_mock: MagicMock,
    event_handler_mock: MagicMock,
    unit_of_work: MagicMock,
    snapshot_store_mock: MagicMock,
) -> ChangePasswordCommandHandler:
    return ChangePasswordCommandHandler(
        event_store=event_store_mock,
        event_handler=event_handler_mock,
        unit_of_work=unit_of_work,
        snapshot_store=snapshot_store_mock,
    )


@pytest.fixture
def change_password_command() -> ChangePasswordCommand:
    return ChangePasswordCommand(
        user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        new_password_hash="new_hashed_password",  # noqa: S106  # pragma: allowlist secret
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
        password_hash="old_hashed_password",  # noqa: S106  # pragma: allowlist secret
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
            "password_hash": "old_hashed_password",  # noqa: S106  # pragma: allowlist secret
            "created_at": "2023-01-01T12:00:00+00:00",
            "updated_at": "2023-01-01T12:00:00+00:00",
            "deleted_at": None,
        },
        revision=2,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


class TestChangePasswordCommandHandler:
    """Unit tests for ChangePasswordCommandHandler"""

    @pytest.mark.asyncio
    async def test_handle_success_without_snapshot(
        self,
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_password_command: ChangePasswordCommand,
        user_created_event: EventDTO,
    ) -> None:
        """Test successful password change without existing snapshot."""
        # Configure mocks
        event_store_mock.get_stream.return_value = [user_created_event]
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = None

        await handler.handle(change_password_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            change_password_command.user_id,
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
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_password_command: ChangePasswordCommand,
        user_snapshot: UserSnapshotDTO,
        user_updated_event: EventDTO,
    ) -> None:
        """Test successful password change with existing snapshot."""
        # Configure mocks
        event_store_mock.get_stream.return_value = [user_updated_event]
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = user_snapshot

        await handler.handle(change_password_command)

        # Verify event store calls with correct start_revision
        event_store_mock.get_stream.assert_awaited_once_with(
            change_password_command.user_id,
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
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_password_command: ChangePasswordCommand,
        user_snapshot: UserSnapshotDTO,
        user_created_event: EventDTO,
        user_updated_event: EventDTO,
    ) -> None:
        """Test that events with lower or equal revision are skipped during replay."""
        # Configure mocks
        # Create events with mixed revisions - some should be skipped
        events = [
            user_created_event,  # revision 1 - should be skipped (<= snapshot revision 2)
            user_updated_event,  # revision 2 - should be skipped (== snapshot revision 2)
        ]
        event_store_mock.get_stream.return_value = events
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = user_snapshot

        await handler.handle(change_password_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            change_password_command.user_id,
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
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_password_command: ChangePasswordCommand,
        user_snapshot: UserSnapshotDTO,
    ) -> None:
        """Test handling when no new events are returned from event store."""
        # Configure mocks - no new events
        event_store_mock.get_stream.return_value = []
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = user_snapshot

        await handler.handle(change_password_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            change_password_command.user_id,
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
        change_password_command: ChangePasswordCommand,
        user_created_event: EventDTO,
    ) -> None:
        """Test handling when no snapshot store is available."""
        # Create handler without snapshot store
        handler = ChangePasswordCommandHandler(
            event_store=event_store_mock,
            event_handler=event_handler_mock,
            unit_of_work=unit_of_work,
            snapshot_store=None,
        )

        # Configure mocks
        event_store_mock.get_stream.return_value = [user_created_event]

        await handler.handle(change_password_command)

        # Verify event store calls
        event_store_mock.get_stream.assert_awaited_once_with(
            change_password_command.user_id,
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
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        change_password_command: ChangePasswordCommand,
    ) -> None:
        """Test that domain errors are propagated."""
        # Configure mocks
        event_store_mock.get_stream.return_value = []
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = None

        # Create command that will cause domain error (empty password)
        bad_command = ChangePasswordCommand(
            user_id=change_password_command.user_id,
            new_password_hash="",  # noqa: S106  # pragma: allowlist secret
        )

        with pytest.raises(ValueError, match="Password is required"):
            await handler.handle(bad_command)

        # Verify no events were persisted
        event_store_mock.append_to_stream.assert_not_awaited()
        event_handler_mock.dispatch.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_with_snapshot_store_error(
        self,
        handler: ChangePasswordCommandHandler,
        event_store_mock: MagicMock,
        event_handler_mock: MagicMock,
        unit_of_work: MagicMock,
        change_password_command: ChangePasswordCommand,
        user_created_event: EventDTO,
    ) -> None:
        """Test handling when snapshot store operations fail."""
        # Configure mocks
        event_store_mock.get_stream.return_value = [user_created_event]
        snapshot_store_mock = handler.snapshot_store
        snapshot_store_mock.get.return_value = None
        snapshot_store_mock.set.side_effect = Exception("Snapshot store error")

        with pytest.raises(Exception, match="Snapshot store error"):
            await handler.handle(change_password_command)

        # Verify event store operations completed
        event_store_mock.get_stream.assert_awaited_once()
        event_store_mock.append_to_stream.assert_awaited_once()
        event_handler_mock.dispatch.assert_awaited_once()

        # Verify unit of work was rolled back due to snapshot error
        unit_of_work.rollback.assert_awaited_once()
        unit_of_work.commit.assert_not_awaited()
