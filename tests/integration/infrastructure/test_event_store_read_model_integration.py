"""Integration tests for Event Store and Read Model interaction.

These tests verify that the PostgreSQL event store and read model
work together correctly, ensuring data consistency and proper
event-driven updates to the read model.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.events.base import EventDTO
from event_sourcing.dto.events.user.user_created import UserCreatedDataV1
from event_sourcing.dto.events.user.user_updated import UserUpdatedDataV1
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.enums import AggregateTypeEnum, EventType

if TYPE_CHECKING:
    from event_sourcing.infrastructure.event_store.psql import (
        PostgreSQLEventStore,
    )
    from event_sourcing.infrastructure.read_model.psql import (
        PostgreSQLReadModel,
    )


class TestEventStoreReadModelIntegration:
    """Integration tests for Event Store and Read Model interaction."""

    @pytest.fixture
    def event_store(self, db: AsyncSession) -> "PostgreSQLEventStore":
        """Create event store instance with test database session."""
        from event_sourcing.infrastructure.event_store.psql import (
            PostgreSQLEventStore,
        )

        return PostgreSQLEventStore(db)

    @pytest.fixture
    def read_model(self, db: AsyncSession) -> "PostgreSQLReadModel":
        """Create read model instance with test database session."""
        from event_sourcing.infrastructure.read_model.psql import (
            PostgreSQLReadModel,
        )

        return PostgreSQLReadModel(db)

    @pytest.fixture
    def sample_user_id(self) -> uuid.UUID:
        """Generate a sample user ID for testing."""
        return uuid.uuid4()

    @pytest.fixture
    def user_created_event(self, sample_user_id: uuid.UUID) -> EventDTO:
        """Create a USER_CREATED event."""
        return EventDTO(
            id=uuid.uuid4(),
            aggregate_id=sample_user_id,
            event_type=EventType.USER_CREATED,
            timestamp=datetime.now(timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password_hash="hashed_password",  # pragma: allowlist secret
            ),
        )

    @pytest.fixture
    def user_updated_event(self, sample_user_id: uuid.UUID) -> EventDTO:
        """Create a USER_UPDATED event."""
        return EventDTO(
            id=uuid.uuid4(),
            aggregate_id=sample_user_id,
            event_type=EventType.USER_UPDATED,
            timestamp=datetime.now(timezone.utc),
            version="1",
            revision=2,
            data=UserUpdatedDataV1(first_name="Updated", last_name="Name"),
        )

    async def test_event_store_and_read_model_consistency(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        user_created_event: EventDTO,
        db: AsyncSession,
    ) -> None:
        """Test that events stored in event store can be used to update read model."""
        # Store event in event store
        await event_store.append_to_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=[user_created_event],
        )
        await db.commit()

        # Verify event is stored
        stored_events = await event_store.get_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
        )
        assert len(stored_events) == 1
        assert stored_events[0].event_type == EventType.USER_CREATED

        # Update read model based on event data
        event_data = user_created_event.data
        read_model_data = UserReadModelData(
            aggregate_id=str(user_created_event.aggregate_id),
            username=event_data.username,
            email=event_data.email,
            first_name=event_data.first_name,
            last_name=event_data.last_name,
            password_hash=event_data.password_hash,
        )

        await read_model.save_user(read_model_data)
        await db.commit()

        # Verify read model is updated
        user = await read_model.get_user(str(user_created_event.aggregate_id))
        assert user is not None
        assert user.username == event_data.username
        assert user.email == event_data.email
        assert user.first_name == event_data.first_name
        assert user.last_name == event_data.last_name

    async def test_multiple_events_update_read_model_correctly(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        user_created_event: EventDTO,
        user_updated_event: EventDTO,
        db: AsyncSession,
    ) -> None:
        """Test that multiple events update the read model correctly in sequence."""
        # Store both events
        await event_store.append_to_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=[user_created_event, user_updated_event],
        )
        await db.commit()

        # Verify events are stored in correct order
        stored_events = await event_store.get_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
        )
        assert len(stored_events) == 2
        assert stored_events[0].revision == 1
        assert stored_events[1].revision == 2

        # Apply events to read model in sequence
        # First event: USER_CREATED
        created_data = user_created_event.data
        read_model_data = UserReadModelData(
            aggregate_id=str(user_created_event.aggregate_id),
            username=created_data.username,
            email=created_data.email,
            first_name=created_data.first_name,
            last_name=created_data.last_name,
            password_hash=created_data.password_hash,
        )
        await read_model.save_user(read_model_data)

        # Second event: USER_UPDATED
        updated_data = user_updated_event.data
        update_read_model_data = UserReadModelData(
            aggregate_id=str(user_created_event.aggregate_id),
            first_name=updated_data.first_name,
            last_name=updated_data.last_name,
        )
        await read_model.save_user(update_read_model_data)
        await db.commit()

        # Verify final state in read model
        user = await read_model.get_user(str(user_created_event.aggregate_id))
        assert user is not None
        assert user.username == created_data.username  # From first event
        assert user.email == created_data.email  # From first event
        assert user.first_name == updated_data.first_name  # From second event
        assert user.last_name == updated_data.last_name  # From second event

    async def test_event_stream_reconstruction_from_read_model(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        user_created_event: EventDTO,
        user_updated_event: EventDTO,
        db: AsyncSession,
    ) -> None:
        """Test that read model can be reconstructed from event stream."""
        # Store events
        await event_store.append_to_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=[user_created_event, user_updated_event],
        )
        await db.commit()

        # Simulate read model reconstruction from events
        stored_events = await event_store.get_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
        )

        # Reconstruct user state from events
        reconstructed_user = None
        for event in stored_events:
            if event.event_type == EventType.USER_CREATED:
                event_data = event.data
                reconstructed_user = UserReadModelData(
                    aggregate_id=str(event.aggregate_id),
                    username=event_data.username,
                    email=event_data.email,
                    first_name=event_data.first_name,
                    last_name=event_data.last_name,
                    password_hash=event_data.password_hash,
                )
            elif event.event_type == EventType.USER_UPDATED:
                event_data = event.data
                if reconstructed_user:
                    if event_data.first_name is not None:
                        reconstructed_user.first_name = event_data.first_name
                    if event_data.last_name is not None:
                        reconstructed_user.last_name = event_data.last_name

        # Save reconstructed user to read model
        if reconstructed_user:
            await read_model.save_user(reconstructed_user)
            await db.commit()

            # Verify reconstruction is correct
            user = await read_model.get_user(
                str(user_created_event.aggregate_id)
            )
            assert user is not None
            assert user.username == user_created_event.data.username
            assert user.email == user_created_event.data.email
            assert user.first_name == user_updated_event.data.first_name
            assert user.last_name == user_updated_event.data.last_name

    async def test_event_search_integration_with_read_model(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        db: AsyncSession,
    ) -> None:
        """Test that event search results can be used to update read model."""
        # Create multiple users with events
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()

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

        # Store events
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
        await db.commit()

        # Search for events by username
        user1_events_found = await event_store.search_events(
            aggregate_type=AggregateTypeEnum.USER,
            query_params={"username": "user1"},
        )

        # Update read model based on search results
        for event in user1_events_found:
            if event.event_type == EventType.USER_CREATED:
                event_data = event.data
                read_model_data = UserReadModelData(
                    aggregate_id=str(event.aggregate_id),
                    username=event_data.username,
                    email=event_data.email,
                    first_name=event_data.first_name,
                    last_name=event_data.last_name,
                    password_hash=event_data.password_hash,
                )
                await read_model.save_user(read_model_data)

        await db.commit()

        # Verify read model was updated
        user1 = await read_model.get_user(str(user1_id))
        assert user1 is not None
        assert user1.username == "user1"

        # User2 should not exist in read model (not processed)
        user2 = await read_model.get_user(str(user2_id))
        assert user2 is None

    async def test_event_time_filtering_with_read_model_updates(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        db: AsyncSession,
    ) -> None:
        """Test that time-filtered events can be used for read model updates."""
        base_time = datetime.now(timezone.utc)

        # Create events at different times
        user_id = uuid.uuid4()
        events = [
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user_id,
                event_type=EventType.USER_CREATED,
                timestamp=base_time,
                version="1",
                revision=1,
                data=UserCreatedDataV1(
                    username="timeuser",
                    email="time@example.com",
                    first_name="Time",
                    last_name="User",
                    password_hash="hash",  # pragma: allowlist secret
                ),
            ),
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user_id,
                event_type=EventType.USER_UPDATED,
                timestamp=base_time + timedelta(seconds=10),
                version="1",
                revision=2,
                data=UserUpdatedDataV1(first_name="Updated"),
            ),
        ]

        # Store events
        await event_store.append_to_stream(
            aggregate_id=user_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=events,
        )
        await db.commit()

        # Get events after a specific time
        mid_time = base_time + timedelta(seconds=5)
        recent_events = await event_store.get_stream(
            aggregate_id=user_id,
            aggregate_type=AggregateTypeEnum.USER,
            start_time=mid_time,
        )

        # Update read model based on recent events only
        for event in recent_events:
            if event.event_type == EventType.USER_UPDATED:
                event_data = event.data
                # First create user with basic data
                read_model_data = UserReadModelData(
                    aggregate_id=str(user_id),
                    username="timeuser",
                    email="time@example.com",
                    first_name="Time",
                    last_name="User",
                    password_hash="hash",  # pragma: allowlist secret
                )
                await read_model.save_user(read_model_data)

                # Then apply update
                update_data = UserReadModelData(
                    aggregate_id=str(user_id), first_name=event_data.first_name
                )
                await read_model.save_user(update_data)

        await db.commit()

        # Verify read model reflects the update
        user = await read_model.get_user(str(user_id))
        assert user is not None
        assert user.first_name == "Updated"

    async def test_event_revision_filtering_with_read_model(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        db: AsyncSession,
    ) -> None:
        """Test that revision-filtered events can be used for read model updates."""
        user_id = uuid.uuid4()

        # Create multiple events with different revisions
        events = [
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user_id,
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=UserCreatedDataV1(
                    username="revuser",
                    email="rev@example.com",
                    first_name="Rev",
                    last_name="User",
                    password_hash="hash",  # pragma: allowlist secret
                ),
            ),
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user_id,
                event_type=EventType.USER_UPDATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=2,
                data=UserUpdatedDataV1(first_name="Updated"),
            ),
            EventDTO(
                id=uuid.uuid4(),
                aggregate_id=user_id,
                event_type=EventType.USER_UPDATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=3,
                data=UserUpdatedDataV1(last_name="Changed"),
            ),
        ]

        # Store events
        await event_store.append_to_stream(
            aggregate_id=user_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=events,
        )
        await db.commit()

        # Get events after revision 1
        recent_events = await event_store.get_stream(
            aggregate_id=user_id,
            aggregate_type=AggregateTypeEnum.USER,
            start_revision=1,
        )

        # Update read model based on recent events only
        # First create user
        read_model_data = UserReadModelData(
            aggregate_id=str(user_id),
            username="revuser",
            email="rev@example.com",
            first_name="Rev",
            last_name="User",
            password_hash="hash",  # pragma: allowlist secret
        )
        await read_model.save_user(read_model_data)

        # Apply updates from recent events
        for event in recent_events:
            if event.event_type == EventType.USER_UPDATED:
                event_data = event.data
                update_data = UserReadModelData(aggregate_id=str(user_id))
                if event_data.first_name is not None:
                    update_data.first_name = event_data.first_name
                if event_data.last_name is not None:
                    update_data.last_name = event_data.last_name

                await read_model.save_user(update_data)

        await db.commit()

        # Verify read model reflects all updates
        user = await read_model.get_user(str(user_id))
        assert user is not None
        assert user.first_name == "Updated"  # From revision 2
        assert user.last_name == "Changed"  # From revision 3

    async def test_event_store_read_model_transaction_consistency(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        user_created_event: EventDTO,
        db: AsyncSession,
    ) -> None:
        """Test that event store and read model maintain consistency within transactions."""
        # Start transaction
        await event_store.append_to_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=[user_created_event],
        )

        # Update read model
        event_data = user_created_event.data
        read_model_data = UserReadModelData(
            aggregate_id=str(user_created_event.aggregate_id),
            username=event_data.username,
            email=event_data.email,
            first_name=event_data.first_name,
            last_name=event_data.last_name,
            password_hash=event_data.password_hash,  # pragma: allowlist secret
        )
        await read_model.save_user(read_model_data)

        # Commit transaction
        await db.commit()

        # Verify both are consistent
        stored_events = await event_store.get_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
        )
        user = await read_model.get_user(str(user_created_event.aggregate_id))

        assert len(stored_events) == 1
        assert user is not None
        assert user.username == stored_events[0].data.username

    async def test_event_store_read_model_rollback_consistency(
        self,
        event_store: "PostgreSQLEventStore",
        read_model: "PostgreSQLReadModel",
        user_created_event: EventDTO,
        db: AsyncSession,
    ) -> None:
        """Test that rollbacks maintain consistency between event store and read model."""
        # Start transaction
        await event_store.append_to_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
            events=[user_created_event],
        )

        # Update read model
        event_data = user_created_event.data
        read_model_data = UserReadModelData(
            aggregate_id=str(user_created_event.aggregate_id),
            username=event_data.username,
            email=event_data.email,
            first_name=event_data.first_name,
            last_name=event_data.last_name,
            password_hash=event_data.password_hash,  # pragma: allowlist secret
        )
        await read_model.save_user(read_model_data)

        # Rollback transaction
        await db.rollback()

        # Verify neither has the data
        stored_events = await event_store.get_stream(
            aggregate_id=user_created_event.aggregate_id,
            aggregate_type=AggregateTypeEnum.USER,
        )
        user = await read_model.get_user(str(user_created_event.aggregate_id))

        assert len(stored_events) == 0
        assert user is None
