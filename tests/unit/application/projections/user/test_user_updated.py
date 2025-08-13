"""Unit tests for UserUpdatedProjection."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from event_sourcing.application.projections.user.user_updated import (
    UserUpdatedProjection,
)
from event_sourcing.dto.events.user.user_updated import (
    UserUpdatedDataV1,
    UserUpdatedV1,
)
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.enums import EventType


class TestUserUpdatedProjection:
    """Test cases for UserUpdatedProjection."""

    @pytest.fixture
    def projection(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> UserUpdatedProjection:
        """Provide a UserUpdatedProjection instance."""
        # Configure the mock for this specific test
        read_model_mock.get_user = AsyncMock()
        read_model_mock.save_user = AsyncMock()
        return UserUpdatedProjection(read_model_mock, unit_of_work)

    @pytest.fixture
    def user_updated_event(self) -> UserUpdatedV1:
        """Provide a sample USER_UPDATED event."""
        return UserUpdatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserUpdatedDataV1(
                first_name="Updated",
                last_name="Name",
                email="updated@example.com",
            ),
        )

    @pytest.fixture
    def existing_user_data(self) -> UserReadModelData:
        """Provide existing user data for testing."""
        return UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="existinguser",
            email="existing@example.com",
            first_name="Existing",
            last_name="User",
            password_hash="existing_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_init(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> None:
        """Test UserUpdatedProjection initialization."""
        projection = UserUpdatedProjection(read_model_mock, unit_of_work)

        assert projection.read_model == read_model_mock
        assert projection.unit_of_work == unit_of_work

    @pytest.mark.asyncio
    async def test_handle_success_with_existing_user(
        self,
        projection: UserUpdatedProjection,
        user_updated_event: UserUpdatedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test successful event handling with existing user."""
        projection.read_model.get_user.return_value = existing_user_data

        await projection.handle(user_updated_event)

        # Verify read model was called to get existing user
        projection.read_model.get_user.assert_awaited_once_with(
            str(user_updated_event.aggregate_id)
        )

        # Verify save_user was called with correct data
        projection.read_model.save_user.assert_awaited_once()
        saved_data = projection.read_model.save_user.call_args[0][0]

        assert isinstance(saved_data, UserReadModelData)
        assert saved_data.aggregate_id == str(user_updated_event.aggregate_id)
        assert saved_data.username == existing_user_data.username  # Preserved
        assert (
            saved_data.first_name == user_updated_event.data.first_name
        )  # Updated
        assert (
            saved_data.last_name == user_updated_event.data.last_name
        )  # Updated
        assert saved_data.email == user_updated_event.data.email  # Updated
        assert saved_data.updated_at == user_updated_event.timestamp
        assert saved_data.created_at is None  # Not set in this projection

        # Verify unit of work was used
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_success_without_existing_user(
        self,
        projection: UserUpdatedProjection,
        user_updated_event: UserUpdatedV1,
    ) -> None:
        """Test successful event handling without existing user."""
        projection.read_model.get_user.return_value = None

        await projection.handle(user_updated_event)

        # Verify read model was called to get existing user
        projection.read_model.get_user.assert_awaited_once_with(
            str(user_updated_event.aggregate_id)
        )

        # Verify save_user was called with correct data
        projection.read_model.save_user.assert_awaited_once()
        saved_data = projection.read_model.save_user.call_args[0][0]

        assert saved_data.username is None  # No existing user to preserve from
        assert saved_data.first_name == user_updated_event.data.first_name
        assert saved_data.last_name == user_updated_event.data.last_name
        assert saved_data.email == user_updated_event.data.email
        assert saved_data.updated_at == user_updated_event.timestamp

    @pytest.mark.asyncio
    async def test_handle_with_get_user_error(
        self,
        projection: UserUpdatedProjection,
        user_updated_event: UserUpdatedV1,
    ) -> None:
        """Test handling when get_user fails."""
        error = Exception("Database error")
        projection.read_model.get_user.side_effect = error

        with pytest.raises(Exception, match="Database error"):
            await projection.handle(user_updated_event)

        # Verify unit of work was NOT entered since get_user failed before the context manager
        projection.unit_of_work.__aenter__.assert_not_awaited()
        projection.unit_of_work.__aexit__.assert_not_awaited()

        # Verify save_user was not called
        projection.read_model.save_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_with_save_user_error(
        self,
        projection: UserUpdatedProjection,
        user_updated_event: UserUpdatedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test handling when save_user fails."""
        projection.read_model.get_user.return_value = existing_user_data
        error = Exception("Save error")
        projection.read_model.save_user.side_effect = error

        with pytest.raises(Exception, match="Save error"):
            await projection.handle(user_updated_event)

        # Verify unit of work was entered and exited
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_unit_of_work_error(
        self,
        projection: UserUpdatedProjection,
        user_updated_event: UserUpdatedV1,
    ) -> None:
        """Test handling when unit of work operations fail."""
        # Mock get_user to succeed but then fail when entering the context manager
        projection.read_model.get_user.return_value = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        error = Exception("UoW error")
        projection.unit_of_work.__aenter__.side_effect = error

        with pytest.raises(Exception, match="UoW error"):
            await projection.handle(user_updated_event)

        # Verify read model was called to get user
        projection.read_model.get_user.assert_awaited_once()

        # Verify save_user was not called since context manager failed
        projection.read_model.save_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_preserves_existing_username(
        self,
        projection: UserUpdatedProjection,
        user_updated_event: UserUpdatedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test that existing username is preserved when updating user."""
        projection.read_model.get_user.return_value = existing_user_data

        await projection.handle(user_updated_event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == existing_user_data.username

    @pytest.mark.asyncio
    async def test_handle_with_partial_updates(
        self, projection: UserUpdatedProjection
    ) -> None:
        """Test handling with partial field updates."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="partialuser",
            email="partial@example.com",
            first_name="Partial",
            last_name="User",
            password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        # Event with only first_name update - other fields will be set to empty strings by the projection
        event = UserUpdatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserUpdatedDataV1(
                first_name="NewFirstName",
                last_name="",  # Empty string will override existing
                email="",  # Empty string will override existing
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == existing_user.username  # Preserved
        assert saved_data.first_name == "NewFirstName"  # Updated
        assert saved_data.last_name == ""  # Set to empty string
        assert saved_data.email == ""  # Set to empty string

    @pytest.mark.asyncio
    async def test_handle_with_none_values(
        self, projection: UserUpdatedProjection
    ) -> None:
        """Test handling with None values in event data."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="noneuser",
            email="none@example.com",
            first_name="None",
            last_name="User",
            password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        # Note: Pydantic models don't allow None for these fields, so we'll test with empty strings instead
        event = UserUpdatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserUpdatedDataV1(
                first_name="",  # Empty string instead of None
                last_name="",  # Empty string instead of None
                email="",  # Empty string instead of None
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == existing_user.username  # Preserved
        assert saved_data.first_name == ""  # Set to empty string
        assert saved_data.last_name == ""  # Set to empty string
        assert saved_data.email == ""  # Set to empty string

    @pytest.mark.asyncio
    async def test_handle_with_empty_strings(
        self, projection: UserUpdatedProjection
    ) -> None:
        """Test handling with empty string values in event data."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="emptyuser",
            email="empty@example.com",
            first_name="Empty",
            last_name="User",
            password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        event = UserUpdatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserUpdatedDataV1(
                first_name="",
                last_name="",
                email="",
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == existing_user.username  # Preserved
        assert saved_data.first_name == ""  # Set to empty string
        assert saved_data.last_name == ""  # Set to empty string
        assert saved_data.email == ""  # Set to empty string

    @pytest.mark.asyncio
    async def test_handle_with_special_characters(
        self, projection: UserUpdatedProjection
    ) -> None:
        """Test handling with special characters in names."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="specialuser",
            email="special@example.com",
            first_name="Special",
            last_name="User",
            password_hash="hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        event = UserUpdatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_UPDATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserUpdatedDataV1(
                first_name="José",
                last_name="O'Connor",
                email="special@example.com",
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.first_name == "José"
        assert saved_data.last_name == "O'Connor"
        assert saved_data.email == "special@example.com"
