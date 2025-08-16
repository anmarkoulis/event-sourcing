"""Unit tests for UserCreatedProjection."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from event_sourcing.application.projections.user.user_created import (
    UserCreatedProjection,
)
from event_sourcing.dto.events.user.user_created import (
    UserCreatedDataV1,
    UserCreatedV1,
)
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.enums import EventType
from event_sourcing.infrastructure.enums import HashingMethod


class TestUserCreatedProjection:
    """Test cases for UserCreatedProjection."""

    @pytest.fixture
    def projection(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> UserCreatedProjection:
        """Provide a UserCreatedProjection instance."""
        # Configure the mock for this specific test
        read_model_mock.save_user = AsyncMock()
        return UserCreatedProjection(read_model_mock, unit_of_work)

    @pytest.fixture
    def user_created_event(self) -> UserCreatedV1:
        """Provide a sample USER_CREATED event."""
        return UserCreatedV1(
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
                password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            ),
        )

    @pytest.mark.asyncio
    async def test_init(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> None:
        """Test UserCreatedProjection initialization."""
        projection = UserCreatedProjection(read_model_mock, unit_of_work)

        assert projection.read_model == read_model_mock
        assert projection.unit_of_work == unit_of_work

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        projection: UserCreatedProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test successful event handling."""
        await projection.handle(user_created_event)

        # Verify read model was called with correct data
        projection.read_model.save_user.assert_awaited_once()
        saved_data = projection.read_model.save_user.call_args[0][0]

        assert isinstance(saved_data, UserReadModelData)
        assert saved_data.aggregate_id == str(user_created_event.aggregate_id)
        assert saved_data.username == user_created_event.data.username
        assert saved_data.email == user_created_event.data.email
        assert saved_data.first_name == user_created_event.data.first_name
        assert saved_data.last_name == user_created_event.data.last_name
        assert saved_data.created_at == user_created_event.timestamp
        assert saved_data.updated_at is None

        # Verify unit of work was used
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_read_model_error(
        self,
        projection: UserCreatedProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test handling when read model operations fail."""
        error = Exception("Database error")
        projection.read_model.save_user.side_effect = error

        with pytest.raises(Exception, match="Database error"):
            await projection.handle(user_created_event)

        # Verify unit of work was entered and exited
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_unit_of_work_error(
        self,
        projection: UserCreatedProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test handling when unit of work operations fail."""
        error = Exception("UoW error")
        projection.unit_of_work.__aenter__.side_effect = error

        with pytest.raises(Exception, match="UoW error"):
            await projection.handle(user_created_event)

        # Verify read model was not called
        projection.read_model.save_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_preserves_event_data_integrity(
        self,
        projection: UserCreatedProjection,
        user_created_event: UserCreatedV1,
    ) -> None:
        """Test that event data is preserved exactly when creating read model data."""
        await projection.handle(user_created_event)

        saved_data = projection.read_model.save_user.call_args[0][0]

        # Verify all event data fields are preserved
        assert saved_data.username == user_created_event.data.username
        assert saved_data.email == user_created_event.data.email
        assert saved_data.first_name == user_created_event.data.first_name
        assert saved_data.last_name == user_created_event.data.last_name

    @pytest.mark.asyncio
    async def test_handle_with_different_event_data(
        self, projection: UserCreatedProjection
    ) -> None:
        """Test handling with different event data values."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 6, 15, 14, 30, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="anotheruser",
                email="another@example.com",
                first_name="Another",
                last_name="Person",
                password_hash="different_hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            ),
        )

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == "anotheruser"
        assert saved_data.email == "another@example.com"
        assert saved_data.first_name == "Another"
        assert saved_data.last_name == "Person"
        assert saved_data.created_at == event.timestamp

    @pytest.mark.asyncio
    async def test_handle_with_empty_names(
        self, projection: UserCreatedProjection
    ) -> None:
        """Test handling with empty first/last names."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="minimaluser",
                email="minimal@example.com",
                first_name="",
                last_name="",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            ),
        )

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.first_name == ""
        assert saved_data.last_name == ""

    @pytest.mark.asyncio
    async def test_handle_with_none_names(
        self, projection: UserCreatedProjection
    ) -> None:
        """Test handling with None first/last names."""
        # Note: Pydantic models don't allow None for these fields, so we'll test with empty strings instead
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="minimaluser",
                email="minimal@example.com",
                first_name="",  # Empty string instead of None
                last_name="",  # Empty string instead of None
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            ),
        )

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.first_name == ""
        assert saved_data.last_name == ""

    @pytest.mark.asyncio
    async def test_handle_with_special_characters(
        self, projection: UserCreatedProjection
    ) -> None:
        """Test handling with special characters in names."""
        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username="special_user",
                email="special@example.com",
                first_name="José",
                last_name="O'Connor",
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            ),
        )

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.first_name == "José"
        assert saved_data.last_name == "O'Connor"

    @pytest.mark.asyncio
    async def test_handle_with_long_values(
        self, projection: UserCreatedProjection
    ) -> None:
        """Test handling with long string values."""
        long_username = "a" * 100
        long_email = "very_long_email_address_that_exceeds_normal_length@very_long_domain_name.com"
        long_first_name = "VeryLongFirstNameThatExceedsNormalLength"
        long_last_name = "VeryLongLastNameThatExceedsNormalLength"

        event = UserCreatedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=UserCreatedDataV1(
                username=long_username,
                email=long_email,
                first_name=long_first_name,
                last_name=long_last_name,
                password_hash="hash",  # noqa: S106  # pragma: allowlist secret
                hashing_method=HashingMethod.BCRYPT,
            ),
        )

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == long_username
        assert saved_data.email == long_email
        assert saved_data.first_name == long_first_name
        assert saved_data.last_name == long_last_name
        assert saved_data.created_at == event.timestamp
