"""Integration tests for PostgreSQL Snapshot Store.

These tests verify that the PostgreSQL snapshot store works correctly
with a real database, testing snapshot persistence, retrieval, and error
handling without any mocking.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.snapshot import SnapshotDTO
from event_sourcing.dto.user import UserDTO
from event_sourcing.enums import AggregateTypeEnum, Role
from event_sourcing.exceptions import UnsupportedAggregateTypeError

if TYPE_CHECKING:
    from event_sourcing.infrastructure.snapshot_store.psql_store import (
        PsqlSnapshotStore,
    )


class TestPsqlSnapshotStore:
    """Integration tests for PostgreSQL Snapshot Store."""

    @pytest.fixture
    def snapshot_store(self, db: AsyncSession) -> "PsqlSnapshotStore":
        """Create snapshot store instance with test database session."""
        from event_sourcing.infrastructure.snapshot_store.psql_store import (
            PsqlSnapshotStore,
        )

        return PsqlSnapshotStore(db)

    @pytest.fixture
    def sample_user_id(self) -> uuid.UUID:
        """Generate a sample user ID for testing."""
        return uuid.uuid4()

    @pytest.fixture
    def sample_user_data(self) -> UserDTO:
        """Create sample user data for testing."""
        return UserDTO(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=Role.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_snapshot_dto(
        self, sample_user_id: uuid.UUID, sample_user_data: UserDTO
    ) -> SnapshotDTO[UserDTO]:
        """Create a sample snapshot DTO for testing."""
        return SnapshotDTO(
            aggregate_id=sample_user_id,
            aggregate_type=AggregateTypeEnum.USER,
            data=sample_user_data.model_dump(
                mode="json"
            ),  # Convert to JSON-serializable dict
            revision=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def test_table_for_supported_aggregate_type(
        self, snapshot_store: "PsqlSnapshotStore"
    ) -> None:
        """Test that _table_for returns correct table for supported aggregate type."""
        # Test with USER aggregate type
        table = snapshot_store._table_for(AggregateTypeEnum.USER)

        # Should return UserSnapshot class
        from event_sourcing.infrastructure.database.models.snapshot import (
            UserSnapshot,
        )

        assert table == UserSnapshot

    async def test_table_for_unsupported_aggregate_type(
        self, snapshot_store: "PsqlSnapshotStore"
    ) -> None:
        """Test that _table_for raises UnsupportedAggregateTypeError for unsupported types."""

        # Create a mock enum value that's not in the _TABLES mapping
        class MockAggregateType:
            def __str__(self) -> str:
                return "UNSUPPORTED_TYPE"

        mock_unsupported_type = MockAggregateType()

        # This should raise UnsupportedAggregateTypeError
        with pytest.raises(UnsupportedAggregateTypeError) as exc_info:
            # We need to temporarily modify the _TABLES to test this
            # Let's test by accessing a key that doesn't exist
            original_tables = snapshot_store._TABLES
            snapshot_store._TABLES = {}
            try:
                # Use the mock_unsupported_type to trigger the error
                snapshot_store._table_for(mock_unsupported_type)
            finally:
                snapshot_store._TABLES = original_tables

        # Verify the error message contains the string representation of the mock type
        assert "UNSUPPORTED_TYPE" in str(exc_info.value)

    async def test_get_snapshot_success(
        self,
        snapshot_store: "PsqlSnapshotStore",
        sample_snapshot_dto: SnapshotDTO[UserDTO],
    ) -> None:
        """Test successfully retrieving a snapshot."""
        # First, set a snapshot
        await snapshot_store.set(sample_snapshot_dto)

        # Then retrieve it
        retrieved_snapshot = await snapshot_store.get(
            aggregate_id=sample_snapshot_dto.aggregate_id,
            aggregate_type=sample_snapshot_dto.aggregate_type,
        )

        # Verify the snapshot was retrieved correctly
        assert retrieved_snapshot is not None
        assert (
            retrieved_snapshot.aggregate_id == sample_snapshot_dto.aggregate_id
        )
        assert (
            retrieved_snapshot.aggregate_type
            == sample_snapshot_dto.aggregate_type
        )
        assert retrieved_snapshot.revision == sample_snapshot_dto.revision
        assert (
            retrieved_snapshot.data["username"]
            == sample_snapshot_dto.data["username"]
        )
        assert (
            retrieved_snapshot.data["email"]
            == sample_snapshot_dto.data["email"]
        )

    async def test_get_snapshot_not_found(
        self, snapshot_store: "PsqlSnapshotStore"
    ) -> None:
        """Test retrieving a snapshot that doesn't exist."""
        non_existent_id = uuid.uuid4()

        retrieved_snapshot = await snapshot_store.get(
            aggregate_id=non_existent_id,
            aggregate_type=AggregateTypeEnum.USER,
        )

        # Should return None for non-existent snapshot
        assert retrieved_snapshot is None

    async def test_set_snapshot_new(
        self,
        snapshot_store: "PsqlSnapshotStore",
        sample_snapshot_dto: SnapshotDTO[UserDTO],
    ) -> None:
        """Test setting a new snapshot."""
        # Set the snapshot
        await snapshot_store.set(sample_snapshot_dto)

        # Verify it was saved by retrieving it
        retrieved_snapshot = await snapshot_store.get(
            aggregate_id=sample_snapshot_dto.aggregate_id,
            aggregate_type=sample_snapshot_dto.aggregate_type,
        )

        assert retrieved_snapshot is not None
        assert (
            retrieved_snapshot.aggregate_id == sample_snapshot_dto.aggregate_id
        )
        assert retrieved_snapshot.revision == sample_snapshot_dto.revision

    async def test_set_snapshot_update_existing(
        self,
        snapshot_store: "PsqlSnapshotStore",
        sample_snapshot_dto: SnapshotDTO[UserDTO],
    ) -> None:
        """Test updating an existing snapshot."""
        # First, set the initial snapshot
        await snapshot_store.set(sample_snapshot_dto)

        # Create an updated snapshot with higher revision
        updated_user_data = UserDTO(
            id=sample_snapshot_dto.data["id"],
            username=sample_snapshot_dto.data["username"],
            email="updated@example.com",  # Changed email
            first_name=sample_snapshot_dto.data["first_name"],
            last_name=sample_snapshot_dto.data["last_name"],
            role=Role.USER,
            created_at=sample_snapshot_dto.data["created_at"],
            updated_at=datetime.now(timezone.utc),
        )

        updated_snapshot = SnapshotDTO(
            aggregate_id=sample_snapshot_dto.aggregate_id,
            aggregate_type=sample_snapshot_dto.aggregate_type,
            data=updated_user_data.model_dump(
                mode="json"
            ),  # Convert to JSON-serializable dict
            revision=2,  # Higher revision
            created_at=sample_snapshot_dto.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        # Update the snapshot
        await snapshot_store.set(updated_snapshot)

        # Verify the update
        retrieved_snapshot = await snapshot_store.get(
            aggregate_id=sample_snapshot_dto.aggregate_id,
            aggregate_type=sample_snapshot_dto.aggregate_type,
        )

        assert retrieved_snapshot is not None
        assert retrieved_snapshot.revision == 2
        assert retrieved_snapshot.data["email"] == "updated@example.com"

    async def test_set_snapshot_with_unsupported_aggregate_type(
        self, snapshot_store: "PsqlSnapshotStore"
    ) -> None:
        """Test that set method properly handles unsupported aggregate types."""
        # Create a snapshot with an unsupported aggregate type
        # We'll test this by temporarily modifying the _TABLES to be empty
        original_tables = snapshot_store._TABLES
        snapshot_store._TABLES = {}

        try:
            sample_snapshot = SnapshotDTO(
                aggregate_id=uuid.uuid4(),
                aggregate_type=AggregateTypeEnum.USER,
                data=UserDTO(
                    id=uuid.uuid4(),
                    username="testuser",
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    role=Role.USER,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ).model_dump(mode="json"),  # Convert to JSON-serializable dict
                revision=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # This should raise UnsupportedAggregateTypeError
            with pytest.raises(UnsupportedAggregateTypeError):
                await snapshot_store.set(sample_snapshot)
        finally:
            snapshot_store._TABLES = original_tables

    async def test_get_snapshot_with_unsupported_aggregate_type(
        self, snapshot_store: "PsqlSnapshotStore"
    ) -> None:
        """Test that get method properly handles unsupported aggregate types."""
        # Test this by temporarily modifying the _TABLES to be empty
        original_tables = snapshot_store._TABLES
        snapshot_store._TABLES = {}

        try:
            # This should raise UnsupportedAggregateTypeError
            with pytest.raises(UnsupportedAggregateTypeError):
                await snapshot_store.get(
                    aggregate_id=uuid.uuid4(),
                    aggregate_type=AggregateTypeEnum.USER,
                )
        finally:
            snapshot_store._TABLES = original_tables

    async def test_snapshot_data_integrity(
        self,
        snapshot_store: "PsqlSnapshotStore",
        sample_snapshot_dto: SnapshotDTO[UserDTO],
    ) -> None:
        """Test that snapshot data maintains integrity through save/retrieve cycle."""
        # Set the snapshot
        await snapshot_store.set(sample_snapshot_dto)

        # Retrieve it
        retrieved_snapshot = await snapshot_store.get(
            aggregate_id=sample_snapshot_dto.aggregate_id,
            aggregate_type=sample_snapshot_dto.aggregate_type,
        )

        assert retrieved_snapshot is not None

        # Verify all data fields are preserved
        original_data = sample_snapshot_dto.data
        retrieved_data = retrieved_snapshot.data

        assert retrieved_data["id"] == original_data["id"]
        assert retrieved_data["username"] == original_data["username"]
        assert retrieved_data["email"] == original_data["email"]
        assert retrieved_data["first_name"] == original_data["first_name"]
        assert retrieved_data["last_name"] == original_data["last_name"]
        assert retrieved_data["role"] == original_data["role"]
        assert retrieved_data["created_at"] == original_data["created_at"]
        assert retrieved_data["updated_at"] == original_data["updated_at"]

    async def test_multiple_snapshots_same_aggregate(
        self,
        snapshot_store: "PsqlSnapshotStore",
        sample_snapshot_dto: SnapshotDTO[UserDTO],
    ) -> None:
        """Test handling multiple snapshots for the same aggregate."""
        # Set initial snapshot
        await snapshot_store.set(sample_snapshot_dto)

        # Create and set multiple revisions
        for revision in range(2, 5):
            updated_user_data = UserDTO(
                id=sample_snapshot_dto.data["id"],
                username=sample_snapshot_dto.data["username"],
                email=f"revision{revision}@example.com",
                first_name=sample_snapshot_dto.data["first_name"],
                last_name=sample_snapshot_dto.data["last_name"],
                role=Role.USER,
                created_at=sample_snapshot_dto.data["created_at"],
                updated_at=datetime.now(timezone.utc),
            )

            updated_snapshot = SnapshotDTO(
                aggregate_id=sample_snapshot_dto.aggregate_id,
                aggregate_type=sample_snapshot_dto.aggregate_type,
                data=updated_user_data.model_dump(
                    mode="json"
                ),  # Convert to JSON-serializable dict
                revision=revision,
                created_at=sample_snapshot_dto.created_at,
                updated_at=datetime.now(timezone.utc),
            )

            await snapshot_store.set(updated_snapshot)

        # Verify the latest revision is retrieved
        final_snapshot = await snapshot_store.get(
            aggregate_id=sample_snapshot_dto.aggregate_id,
            aggregate_type=sample_snapshot_dto.aggregate_type,
        )

        assert final_snapshot is not None
        assert final_snapshot.revision == 4
        assert final_snapshot.data["email"] == "revision4@example.com"
