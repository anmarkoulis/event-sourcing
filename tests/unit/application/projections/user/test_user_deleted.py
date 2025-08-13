"""Unit tests for UserDeletedProjection."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from event_sourcing.application.projections.user.user_deleted import (
    UserDeletedProjection,
)
from event_sourcing.dto.events.user.user_deleted import (
    UserDeletedDataV1,
    UserDeletedV1,
)
from event_sourcing.enums import EventType


class TestUserDeletedProjection:
    """Test cases for UserDeletedProjection."""

    @pytest.fixture
    def projection(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> UserDeletedProjection:
        """Provide a UserDeletedProjection instance."""
        # Configure the mock for this specific test
        read_model_mock.delete_user = AsyncMock()
        return UserDeletedProjection(read_model_mock, unit_of_work)

    @pytest.fixture
    def user_deleted_event(self) -> UserDeletedV1:
        """Provide a sample USER_DELETED event."""
        return UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )

    @pytest.mark.asyncio
    async def test_init(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> None:
        """Test UserDeletedProjection initialization."""
        projection = UserDeletedProjection(read_model_mock, unit_of_work)

        assert projection.read_model == read_model_mock
        assert projection.unit_of_work == unit_of_work

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        projection: UserDeletedProjection,
        user_deleted_event: UserDeletedV1,
    ) -> None:
        """Test successful event handling."""
        await projection.handle(user_deleted_event)

        # Verify read model was called with correct aggregate ID
        projection.read_model.delete_user.assert_awaited_once_with(
            str(user_deleted_event.aggregate_id)
        )

        # Verify unit of work was used
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_delete_user_error(
        self,
        projection: UserDeletedProjection,
        user_deleted_event: UserDeletedV1,
    ) -> None:
        """Test handling when delete_user fails."""
        error = Exception("Database error")
        projection.read_model.delete_user.side_effect = error

        with pytest.raises(Exception, match="Database error"):
            await projection.handle(user_deleted_event)

        # Verify unit of work was entered and exited
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_unit_of_work_error(
        self,
        projection: UserDeletedProjection,
        user_deleted_event: UserDeletedV1,
    ) -> None:
        """Test handling when unit of work operations fail."""
        error = Exception("UoW error")
        projection.unit_of_work.__aenter__.side_effect = error

        with pytest.raises(Exception, match="UoW error"):
            await projection.handle(user_deleted_event)

        # Verify read model was not called
        projection.read_model.delete_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_with_different_aggregate_id(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with different aggregate ID."""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 6, 15, 14, 30, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(
            str(event.aggregate_id)
        )

    @pytest.mark.asyncio
    async def test_handle_with_specific_aggregate_id(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with a specific aggregate ID."""
        specific_id = "22222222-2222-2222-2222-222222222222"
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )
        # Override the aggregate_id for testing
        event.aggregate_id = specific_id

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(specific_id)

    @pytest.mark.asyncio
    async def test_handle_with_nil_uuid(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with nil UUID."""
        nil_uuid = "00000000-0000-0000-0000-000000000000"
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )
        # Override the aggregate_id for testing
        event.aggregate_id = nil_uuid

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(nil_uuid)

    @pytest.mark.asyncio
    async def test_handle_with_long_uuid_string(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with long UUID string representation."""
        long_uuid = "a" * 100  # Very long string
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )
        # Override the aggregate_id for testing
        event.aggregate_id = long_uuid

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(long_uuid)

    @pytest.mark.asyncio
    async def test_handle_with_special_characters_in_uuid(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with special characters in UUID string."""
        special_uuid = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )
        # Override the aggregate_id for testing
        event.aggregate_id = special_uuid

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(
            special_uuid
        )

    @pytest.mark.asyncio
    async def test_handle_with_empty_uuid_string(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with empty UUID string."""
        empty_uuid = ""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )
        # Override the aggregate_id for testing
        event.aggregate_id = empty_uuid

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(empty_uuid)

    @pytest.mark.asyncio
    async def test_handle_with_none_uuid(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with None UUID."""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )
        # Override the aggregate_id for testing
        event.aggregate_id = None

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with("None")

    @pytest.mark.asyncio
    async def test_handle_with_different_timestamp(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with different timestamp."""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(
            str(event.aggregate_id)
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_version(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with different version."""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="2",
            revision=1,
            data=UserDeletedDataV1(),
        )

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(
            str(event.aggregate_id)
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_revision(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with different revision."""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=999,
            data=UserDeletedDataV1(),
        )

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(
            str(event.aggregate_id)
        )

    @pytest.mark.asyncio
    async def test_handle_with_different_event_id(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling with different event ID."""
        event = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )

        await projection.handle(event)

        projection.read_model.delete_user.assert_awaited_once_with(
            str(event.aggregate_id)
        )

    @pytest.mark.asyncio
    async def test_handle_multiple_times(
        self, projection: UserDeletedProjection
    ) -> None:
        """Test handling multiple events."""
        event1 = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserDeletedDataV1(),
        )

        event2 = UserDeletedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_DELETED,
            timestamp=datetime(2023, 1, 1, 13, 0, tzinfo=timezone.utc),
            version="1",
            revision=2,
            data=UserDeletedDataV1(),
        )

        await projection.handle(event1)
        await projection.handle(event2)

        # Verify both calls were made
        assert projection.read_model.delete_user.await_count == 2
        projection.read_model.delete_user.assert_any_call(
            str(event1.aggregate_id)
        )
        projection.read_model.delete_user.assert_any_call(
            str(event2.aggregate_id)
        )
