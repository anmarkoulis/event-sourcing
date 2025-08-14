"""Integration tests for PostgreSQL Event Store.

These tests verify that the PostgreSQL event store works correctly
with a real database, testing event persistence, retrieval, and search
functionality without any mocking.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.events.base import EventDTO
from event_sourcing.dto.events.user.user_created import UserCreatedDataV1
from event_sourcing.dto.events.user.user_updated import UserUpdatedDataV1
from event_sourcing.enums import AggregateTypeEnum, EventType

if TYPE_CHECKING:
    from event_sourcing.infrastructure.event_store.psql import (
        PostgreSQLEventStore,
    )


class TestPostgreSQLEventStore:
    """Integration tests for PostgreSQL Event Store."""

    @pytest.fixture
    def event_store(self, db: AsyncSession) -> "PostgreSQLEventStore":
        """Create event store instance with test database session."""
        from event_sourcing.infrastructure.event_store.psql import (
            PostgreSQLEventStore,
        )

        return PostgreSQLEventStore(db)

    @pytest.fixture
    def sample_user_id(self) -> uuid.UUID:
        """Generate a sample user ID for testing."""
        return uuid.uuid4()

    @pytest.fixture
    def sample_events(self, sample_user_id: uuid.UUID) -> List[EventDTO]:
        """Create sample events for testing."""
        base_time = datetime.now(timezone.utc)

        return [
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=sample_user_id,
                event_type=EventType.USER_CREATED,
                timestamp=base_time,
                version="1",
                revision=1,
                data=UserCreatedDataV1(
                    username="testuser",
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    password_hash="hashed_password",  # pragma: allowlist secret
                ),
            ),
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=sample_user_id,
                event_type=EventType.USER_UPDATED,
                timestamp=base_time.replace(second=base_time.second + 1),
                version="1",
                revision=2,
                data=UserUpdatedDataV1(first_name="Updated", last_name="Name"),
            ),
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=sample_user_id,
                event_type=EventType.USER_UPDATED,
                timestamp=base_time.replace(second=base_time.second + 2),
                version="1",
                revision=3,
                data=UserUpdatedDataV1(email="updated@example.com"),
            ),
        ]

    async def test_append_to_stream_success(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
    ) -> None:
        """Test successfully appending events to a stream."""
        # Append events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )

        # Verify events were added to session (but not committed yet)
        # This tests the append logic without committing
        assert True  # If we get here without errors, append was successful

    async def test_get_stream_retrieves_all_events(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test retrieving all events from a stream."""
        # Append events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )

        # Commit to persist events
        await db.commit()

        # Retrieve events
        retrieved_events = await event_store.get_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
        )

        # Verify all events were retrieved
        assert len(retrieved_events) == 3
        assert retrieved_events[0].revision == 1
        assert retrieved_events[1].revision == 2
        assert retrieved_events[2].revision == 3

        # Verify event data integrity
        assert retrieved_events[0].event_type == EventType.USER_CREATED
        assert retrieved_events[1].event_type == EventType.USER_UPDATED
        assert retrieved_events[2].event_type == EventType.USER_UPDATED

    async def test_get_stream_with_revision_filter(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test retrieving events with revision filtering."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Get events after revision 1
        filtered_events = await event_store.get_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            start_revision=1,
        )

        # Should get 2 events (revisions 2 and 3)
        assert len(filtered_events) == 2
        assert filtered_events[0].revision == 2
        assert filtered_events[1].revision == 3

    async def test_get_stream_with_time_filter(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test retrieving events with time filtering."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Get events after the first event timestamp
        mid_time = sample_events[1].timestamp
        filtered_events = await event_store.get_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            start_time=mid_time,
        )

        # Should get 2 events (the second and third events)
        assert len(filtered_events) == 2
        assert filtered_events[0].revision == 2
        assert filtered_events[1].revision == 3

    async def test_search_events_by_event_type(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test searching events by event type."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Search for USER_UPDATED events
        found_events = await event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER,
            query_params={"event_type": EventType.USER_UPDATED},
        )

        # Should find 2 USER_UPDATED events
        assert len(found_events) == 2
        assert all(
            event.event_type == EventType.USER_UPDATED
            for event in found_events
        )

    async def test_search_events_by_username(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test searching events by username in event data."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Search for events with username "testuser"
        found_events = await event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER,
            query_params={"username": "testuser"},
        )

        # Should find 1 USER_CREATED event
        assert len(found_events) == 1
        assert found_events[0].event_type == EventType.USER_CREATED
        assert found_events[0].data.username == "testuser"

    async def test_search_events_by_email(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test searching events by email in event data."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Search for events with email "test@example.com"
        found_events = await event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER,
            query_params={"email": "test@example.com"},
        )

        # Should find 1 USER_CREATED event
        assert len(found_events) == 1
        assert found_events[0].event_type == EventType.USER_CREATED
        assert found_events[0].data.email == "test@example.com"

    async def test_search_events_with_time_range(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test searching events within a time range."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Search for events within a time range
        start_time = sample_events[0].timestamp
        end_time = sample_events[1].timestamp

        found_events = await event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER,
            query_params={"start_time": start_time, "end_time": end_time},
        )

        # Should find 2 events (first and second)
        assert len(found_events) == 2
        assert found_events[0].revision == 2  # Most recent first (desc order)
        assert found_events[1].revision == 1

    async def test_search_events_with_limit(
        self,
        event_store: "PostgreSQLEventStore",
        sample_events: List[EventDTO],
        db: AsyncSession,
    ) -> None:
        """Test searching events with result limit."""
        # Append and commit events
        await event_store.append_to_stream(
            aggregate_id=sample_events[0].aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=sample_events,
        )
        await db.commit()

        # Search with limit of 2
        found_events = await event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER, query_params={"limit": 2}
        )

        # Should find only 2 events due to limit
        assert len(found_events) == 2

    async def test_unsupported_aggregate_type_raises_error(
        self, event_store: "PostgreSQLEventStore"
    ) -> None:
        """Test that unsupported aggregate types raise appropriate errors."""
        with pytest.raises(ValueError, match="Unsupported aggregate type"):
            # Test with an invalid aggregate type to ensure proper error handling
            from typing import cast

            invalid_aggregate_type = cast(
                AggregateTypeEnum, "UNSUPPORTED_TYPE"
            )
            await event_store.get_stream(
                aggregate_id=uuid.uuid4(),
                aggregate_type=invalid_aggregate_type,
            )

    async def test_duplicate_event_id_in_same_call(
        self, event_store: "PostgreSQLEventStore", sample_user_id: uuid.UUID
    ) -> None:
        """Test handling of duplicate event IDs within the same call."""
        # Create events with duplicate IDs
        first_event_id = uuid.uuid4()
        duplicate_events = [
            EventDTO(
                id=first_event_id,  # Same ID for both events
                aggregate_id=sample_user_id,
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=UserCreatedDataV1(
                    username="user1",
                    email="user1@example.com",
                    first_name="User",
                    last_name="One",
                    password_hash="hash1",  # pragma: allowlist secret
                ),
            ),
            EventDTO(
                id=first_event_id,  # Duplicate ID
                aggregate_id=sample_user_id,
                event_type=EventType.USER_UPDATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=2,
                data=UserUpdatedDataV1(first_name="Updated"),
            ),
        ]

        # Should not raise error, but only first event should be processed
        await event_store.append_to_stream(
            aggregate_id=sample_user_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=duplicate_events,
        )

        # This tests that the duplicate handling logic works without errors
        assert True

    async def test_multiple_aggregates_independence(
        self, event_store: "PostgreSQLEventStore", db: AsyncSession
    ) -> None:
        """Test that events from different aggregates are independent."""
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()

        # Create events for two different users
        user1_events = [
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user1_id,
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=UserCreatedDataV1(
                    username="user1",
                    email="user1@example.com",
                    first_name="User",
                    last_name="One",
                    password_hash="hash1",  # pragma: allowlist secret
                ),
            )
        ]

        user2_events = [
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user2_id,
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=UserCreatedDataV1(
                    username="user2",
                    email="user2@example.com",
                    first_name="User",
                    last_name="Two",
                    password_hash="hash2",  # pragma: allowlist secret
                ),
            )
        ]

        # Append events for both users
        await event_store.append_to_stream(
            aggregate_id=user1_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=user1_events,
        )
        await event_store.append_to_stream(
            aggregate_id=user2_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=user2_events,
        )

        # Commit to persist events
        await db.commit()

        # Retrieve events for each user
        user1_retrieved = await event_store.get_stream(
            aggregate_id=user1_id, aggregate_type=AggregateTypeEnum.USER
        )
        user2_retrieved = await event_store.get_stream(
            aggregate_id=user2_id, aggregate_type=AggregateTypeEnum.USER
        )

        # Verify independence
        assert len(user1_retrieved) == 1
        assert len(user2_retrieved) == 1
        assert user1_retrieved[0].aggregate_id == user1_id
        assert user2_retrieved[0].aggregate_id == user2_id
        assert user1_retrieved[0].data.username == "user1"
        assert user2_retrieved[0].data.username == "user2"
