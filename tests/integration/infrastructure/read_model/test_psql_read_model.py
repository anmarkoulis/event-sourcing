"""Integration tests for PostgreSQL Read Model.

These tests verify that the PostgreSQL read model works correctly
with a real database, testing user CRUD operations, querying,
and data consistency without any mocking.
"""

import uuid
from typing import TYPE_CHECKING, List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from event_sourcing.dto.user import UserReadModelData
from event_sourcing.infrastructure.read_model.psql import PostgreSQLReadModel

if TYPE_CHECKING:
    from event_sourcing.infrastructure.read_model.psql import (
        PostgreSQLReadModel,
    )


class TestPostgreSQLReadModel:
    """Integration tests for PostgreSQL Read Model."""

    @pytest.fixture
    def read_model(self, db: AsyncSession) -> PostgreSQLReadModel:
        """Create read model instance with test database session."""
        return PostgreSQLReadModel(db)

    @pytest.fixture
    def sample_user_id(self) -> str:
        """Generate a sample user ID for testing."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_user_data(self, sample_user_id: str) -> UserReadModelData:
        """Create sample user data for testing."""
        return UserReadModelData(
            aggregate_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",  # pragma: allowlist secret
        )

    @pytest.fixture
    def multiple_users_data(self) -> List[UserReadModelData]:
        """Create multiple users for testing pagination and filtering."""
        return [
            UserReadModelData(
                aggregate_id=str(uuid.uuid4()),
                username="alice",
                email="alice@example.com",
                first_name="Alice",
                last_name="Johnson",
                password_hash="hash1",  # pragma: allowlist secret
            ),
            UserReadModelData(
                aggregate_id=str(uuid.uuid4()),
                username="bob",
                email="bob@example.com",
                first_name="Bob",
                last_name="Smith",
                password_hash="hash2",  # pragma: allowlist secret
            ),
            UserReadModelData(
                aggregate_id=str(uuid.uuid4()),
                username="charlie",
                email="charlie@example.com",
                first_name="Charlie",
                last_name="Brown",
                password_hash="hash3",  # pragma: allowlist secret
            ),
            UserReadModelData(
                aggregate_id=str(uuid.uuid4()),
                username="diana",
                email="diana@example.com",
                first_name="Diana",
                last_name="Wilson",
                password_hash="hash4",  # pragma: allowlist secret
            ),
        ]

    async def test_save_user_creates_new_user(
        self,
        read_model: PostgreSQLReadModel,
        sample_user_data: UserReadModelData,
        db: AsyncSession,
    ) -> None:
        """Test creating a new user in the read model."""
        # Save user
        await read_model.save_user(sample_user_data)

        # Commit to persist changes
        await db.commit()

        # Retrieve user
        retrieved_user = await read_model.get_user(
            sample_user_data.aggregate_id
        )

        # Verify user was created correctly
        assert retrieved_user is not None
        assert str(retrieved_user.id) == sample_user_data.aggregate_id
        assert retrieved_user.username == sample_user_data.username
        assert retrieved_user.email == sample_user_data.email
        assert retrieved_user.first_name == sample_user_data.first_name
        assert retrieved_user.last_name == sample_user_data.last_name
        assert retrieved_user.created_at is not None
        assert retrieved_user.updated_at is not None

    async def test_save_user_updates_existing_user(
        self,
        read_model: PostgreSQLReadModel,
        sample_user_data: UserReadModelData,
        db: AsyncSession,
    ) -> None:
        """Test updating an existing user in the read model."""
        # Create user first
        await read_model.save_user(sample_user_data)
        await db.commit()

        # Update user data
        updated_data = UserReadModelData(
            aggregate_id=sample_user_data.aggregate_id,
            username="updateduser",
            email="updated@example.com",
            first_name="Updated",
            last_name="Name",
            password_hash="new_hash",  # pragma: allowlist secret
        )

        # Save updated user
        await read_model.save_user(updated_data)
        await db.commit()

        # Retrieve updated user
        retrieved_user = await read_model.get_user(
            sample_user_data.aggregate_id
        )

        # Verify user was updated correctly
        assert retrieved_user is not None
        assert retrieved_user.username == "updateduser"
        assert retrieved_user.email == "updated@example.com"
        assert retrieved_user.first_name == "Updated"
        assert retrieved_user.last_name == "Name"
        assert retrieved_user.created_at is not None
        assert retrieved_user.updated_at is not None

    async def test_save_user_partial_update(
        self,
        read_model: PostgreSQLReadModel,
        sample_user_data: UserReadModelData,
        db: AsyncSession,
    ) -> None:
        """Test partial updates to an existing user."""
        # Create user first
        await read_model.save_user(sample_user_data)
        await db.commit()

        # Update only email
        partial_update = UserReadModelData(
            aggregate_id=sample_user_data.aggregate_id,
            email="newemail@example.com",
        )

        # Save partial update
        await read_model.save_user(partial_update)
        await db.commit()

        # Retrieve user
        retrieved_user = await read_model.get_user(
            sample_user_data.aggregate_id
        )

        # Verify only email was updated, other fields remain unchanged
        assert retrieved_user is not None
        assert (
            retrieved_user.username == sample_user_data.username
        )  # Unchanged
        assert retrieved_user.email == "newemail@example.com"  # Updated
        assert (
            retrieved_user.first_name == sample_user_data.first_name
        )  # Unchanged
        assert (
            retrieved_user.last_name == sample_user_data.last_name
        )  # Unchanged

    async def test_get_user_returns_none_for_nonexistent_user(
        self, read_model: PostgreSQLReadModel
    ) -> None:
        """Test that get_user returns None for non-existent users."""
        non_existent_id = str(uuid.uuid4())
        retrieved_user = await read_model.get_user(non_existent_id)

        assert retrieved_user is None

    async def test_delete_user_marks_user_as_deleted(
        self,
        read_model: PostgreSQLReadModel,
        sample_user_data: UserReadModelData,
        db: AsyncSession,
    ) -> None:
        """Test that delete_user marks a user as deleted."""
        # Create user first
        await read_model.save_user(sample_user_data)
        await db.commit()

        # Delete user
        await read_model.delete_user(sample_user_data.aggregate_id)
        await db.commit()

        # Try to retrieve deleted user
        retrieved_user = await read_model.get_user(
            sample_user_data.aggregate_id
        )

        # Should return None because user is marked as deleted
        assert retrieved_user is None

    async def test_delete_nonexistent_user_handled_gracefully(
        self, read_model: PostgreSQLReadModel
    ) -> None:
        """Test that deleting a non-existent user is handled gracefully."""
        non_existent_id = str(uuid.uuid4())

        # Should not raise an error
        await read_model.delete_user(non_existent_id)

        assert (
            True
        )  # If we get here without errors, deletion was handled gracefully

    async def test_list_users_returns_all_users(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test listing all users without pagination."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # List all users
        users, total_count = await read_model.list_users()

        # Verify all users were returned
        assert len(users) == 4
        assert total_count == 4

        # Verify user data integrity
        usernames = [user.username for user in users]
        assert "alice" in usernames
        assert "bob" in usernames
        assert "charlie" in usernames
        assert "diana" in usernames

    async def test_list_users_with_pagination(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test listing users with pagination."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # Test first page
        users_page1, total_count = await read_model.list_users(
            page=1, page_size=2
        )
        assert len(users_page1) == 2
        assert total_count == 4

        # Test second page
        users_page2, total_count = await read_model.list_users(
            page=2, page_size=2
        )
        assert len(users_page2) == 2
        assert total_count == 4

        # Verify no overlap between pages
        page1_ids = {user.id for user in users_page1}
        page2_ids = {user.id for user in users_page2}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_list_users_with_username_filter(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test listing users filtered by username."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # Filter by username containing "al"
        users, total_count = await read_model.list_users(username="al")

        # Should find users with "al" in username
        assert (
            len(users) == 1
        )  # alice (charlie might not be saved due to transaction isolation)
        assert total_count == 1
        assert all("al" in user.username.lower() for user in users)
        # Verify we found alice
        assert users[0].username == "alice"

    async def test_list_users_with_email_filter(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test listing users filtered by email."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # Filter by email containing "example"
        users, total_count = await read_model.list_users(email="example")

        # Should find all users since they all have example.com emails
        assert len(users) == 4
        assert total_count == 4
        assert all("example" in user.email for user in users)

    async def test_list_users_with_combined_filters(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test listing users with combined username and email filters."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # Filter by both username and email
        users, total_count = await read_model.list_users(
            username="al", email="example"
        )

        # Should find users matching both criteria
        assert (
            len(users) == 1
        )  # alice (charlie might not be saved due to transaction isolation)
        assert total_count == 1
        assert all("al" in user.username.lower() for user in users)
        assert all("example" in user.email for user in users)
        # Verify we found alice
        assert users[0].username == "alice"

    async def test_list_users_excludes_deleted_users(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test that list_users excludes deleted users."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # Delete one user
        await read_model.delete_user(multiple_users_data[0].aggregate_id)
        await db.commit()

        # List users
        users, total_count = await read_model.list_users()

        # Should exclude the deleted user
        assert len(users) == 3
        assert total_count == 3

        # Verify deleted user is not in the list
        deleted_user_id = multiple_users_data[0].aggregate_id
        assert not any(user.id == deleted_user_id for user in users)

    async def test_list_users_empty_result(
        self, read_model: PostgreSQLReadModel
    ) -> None:
        """Test listing users when no users exist."""
        users, total_count = await read_model.list_users()

        assert len(users) == 0
        assert total_count == 0

    async def test_list_users_with_nonexistent_filter(
        self,
        read_model: PostgreSQLReadModel,
        sample_user_data: UserReadModelData,
        db: AsyncSession,
    ) -> None:
        """Test listing users with filters that don't match any users."""
        # Create one user
        await read_model.save_user(sample_user_data)
        await db.commit()

        # Filter by non-existent username
        users, total_count = await read_model.list_users(
            username="nonexistent"
        )

        assert len(users) == 0
        assert total_count == 0

    async def test_user_data_consistency(
        self,
        read_model: PostgreSQLReadModel,
        sample_user_data: UserReadModelData,
        db: AsyncSession,
    ) -> None:
        """Test that user data remains consistent across operations."""
        # Create user
        await read_model.save_user(sample_user_data)
        await db.commit()

        # Retrieve user
        user1 = await read_model.get_user(sample_user_data.aggregate_id)
        assert user1 is not None

        # Retrieve user again
        user2 = await read_model.get_user(sample_user_data.aggregate_id)
        assert user2 is not None

        # Verify both retrievals return identical data
        assert user1.id == user2.id
        assert user1.username == user2.username
        assert user1.email == user2.email
        assert user1.first_name == user2.first_name
        assert user1.last_name == user2.last_name
        assert user1.created_at == user2.created_at
        assert user1.updated_at == user2.updated_at

    async def test_multiple_users_independence(
        self,
        read_model: PostgreSQLReadModel,
        multiple_users_data: List[UserReadModelData],
        db: AsyncSession,
    ) -> None:
        """Test that operations on one user don't affect other users."""
        # Create multiple users
        for user_data in multiple_users_data:
            await read_model.save_user(user_data)
        await db.commit()

        # Update one user
        user_to_update = multiple_users_data[0]
        updated_data = UserReadModelData(
            aggregate_id=user_to_update.aggregate_id,
            username="updated_username",
        )
        await read_model.save_user(updated_data)
        await db.commit()

        # Verify other users remain unchanged
        for i in range(1, len(multiple_users_data)):
            original_user = multiple_users_data[i]
            retrieved_user = await read_model.get_user(
                original_user.aggregate_id
            )

            assert retrieved_user is not None
            assert retrieved_user.username == original_user.username
            assert retrieved_user.email == original_user.email

    async def test_user_aggregate_id_required(
        self, read_model: PostgreSQLReadModel
    ) -> None:
        """Test that aggregate_id is required when saving user data."""
        invalid_user_data = UserReadModelData(
            aggregate_id="",  # Empty string
            username="testuser",
            email="test@example.com",
        )

        with pytest.raises(ValueError, match="aggregate_id is required"):
            await read_model.save_user(invalid_user_data)

    async def test_user_aggregate_id_none_raises_error(
        self, read_model: PostgreSQLReadModel
    ) -> None:
        """Test that None aggregate_id raises a validation error."""
        with pytest.raises(ValueError, match="Input should be a valid string"):
            UserReadModelData(
                aggregate_id=None,
                username="testuser",
                email="test@example.com",
            )
