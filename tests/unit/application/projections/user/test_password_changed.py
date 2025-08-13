"""Unit tests for PasswordChangedProjection."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from event_sourcing.application.projections.user.password_changed import (
    PasswordChangedProjection,
)
from event_sourcing.dto.events.user.password_changed import (
    PasswordChangedDataV1,
    PasswordChangedV1,
)
from event_sourcing.dto.user import UserReadModelData
from event_sourcing.enums import EventType


class TestPasswordChangedProjection:
    """Test cases for PasswordChangedProjection."""

    @pytest.fixture
    def projection(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> PasswordChangedProjection:
        """Provide a PasswordChangedProjection instance."""
        # Configure the mock for this specific test
        read_model_mock.get_user = AsyncMock()
        read_model_mock.save_user = AsyncMock()
        return PasswordChangedProjection(read_model_mock, unit_of_work)

    @pytest.fixture
    def password_changed_event(self) -> PasswordChangedV1:
        """Provide a sample PASSWORD_CHANGED event."""
        return PasswordChangedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=PasswordChangedDataV1(
                password_hash="new_hashed_password",  # noqa: S106  # pragma: allowlist secret
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
            password_hash="old_hashed_password",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_init(
        self, read_model_mock: MagicMock, unit_of_work: MagicMock
    ) -> None:
        """Test PasswordChangedProjection initialization."""
        projection = PasswordChangedProjection(read_model_mock, unit_of_work)

        assert projection.read_model == read_model_mock
        assert projection.unit_of_work == unit_of_work

    @pytest.mark.asyncio
    async def test_handle_success_with_existing_user(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test successful event handling with existing user."""
        projection.read_model.get_user.return_value = existing_user_data

        await projection.handle(password_changed_event)

        # Verify read model was called to get existing user
        projection.read_model.get_user.assert_awaited_once_with(
            str(password_changed_event.aggregate_id)
        )

        # Verify save_user was called with correct data
        projection.read_model.save_user.assert_awaited_once()
        saved_data = projection.read_model.save_user.call_args[0][0]

        assert isinstance(saved_data, UserReadModelData)
        assert saved_data.aggregate_id == str(
            password_changed_event.aggregate_id
        )
        assert saved_data.username == existing_user_data.username  # Preserved
        assert (
            saved_data.password_hash
            == password_changed_event.data.password_hash
        )  # Updated
        assert saved_data.updated_at == password_changed_event.timestamp
        assert saved_data.created_at is None  # Not set in this projection

        # Verify unit of work was used
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_success_without_existing_user(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
    ) -> None:
        """Test successful event handling without existing user."""
        projection.read_model.get_user.return_value = None

        await projection.handle(password_changed_event)

        # Verify read model was called to get existing user
        projection.read_model.get_user.assert_awaited_once_with(
            str(password_changed_event.aggregate_id)
        )

        # Verify save_user was called with correct data
        projection.read_model.save_user.assert_awaited_once()
        saved_data = projection.read_model.save_user.call_args[0][0]

        assert saved_data.username is None  # No existing user to preserve from
        assert (
            saved_data.password_hash
            == password_changed_event.data.password_hash
        )
        assert saved_data.updated_at == password_changed_event.timestamp

    @pytest.mark.asyncio
    async def test_handle_with_get_user_error(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
    ) -> None:
        """Test handling when get_user fails."""
        error = Exception("Database error")
        projection.read_model.get_user.side_effect = error

        with pytest.raises(Exception, match="Database error"):
            await projection.handle(password_changed_event)

        # Verify unit of work was NOT entered since get_user failed before the context manager
        projection.unit_of_work.__aenter__.assert_not_awaited()
        projection.unit_of_work.__aexit__.assert_not_awaited()

        # Verify save_user was not called
        projection.read_model.save_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_with_save_user_error(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test handling when save_user fails."""
        projection.read_model.get_user.return_value = existing_user_data
        error = Exception("Save error")
        projection.read_model.save_user.side_effect = error

        with pytest.raises(Exception, match="Save error"):
            await projection.handle(password_changed_event)

        # Verify unit of work was entered and exited
        projection.unit_of_work.__aenter__.assert_awaited_once()
        projection.unit_of_work.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_with_unit_of_work_error(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
    ) -> None:
        """Test handling when unit of work operations fail."""
        # Mock get_user to succeed but then fail when entering the context manager
        projection.read_model.get_user.return_value = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="old_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        error = Exception("UoW error")
        projection.unit_of_work.__aenter__.side_effect = error

        with pytest.raises(Exception, match="UoW error"):
            await projection.handle(password_changed_event)

        # Verify read model was called to get user
        projection.read_model.get_user.assert_awaited_once()

        # Verify save_user was not called since context manager failed
        projection.read_model.save_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_preserves_existing_username(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test that existing username is preserved when updating password."""
        projection.read_model.get_user.return_value = existing_user_data

        await projection.handle(password_changed_event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.username == existing_user_data.username

    @pytest.mark.asyncio
    async def test_handle_updates_password_hash(
        self,
        projection: PasswordChangedProjection,
        password_changed_event: PasswordChangedV1,
        existing_user_data: UserReadModelData,
    ) -> None:
        """Test that password hash is updated correctly."""
        projection.read_model.get_user.return_value = existing_user_data

        await projection.handle(password_changed_event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert (
            saved_data.password_hash
            == password_changed_event.data.password_hash
        )
        assert saved_data.password_hash != existing_user_data.password_hash

    @pytest.mark.asyncio
    async def test_handle_with_different_password_hash(
        self, projection: PasswordChangedProjection
    ) -> None:
        """Test handling with different password hash values."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="passworduser",
            email="password@example.com",
            first_name="Password",
            last_name="User",
            password_hash="old_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        event = PasswordChangedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=PasswordChangedDataV1(
                password_hash="completely_different_hash",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.password_hash == "completely_different_hash"  # noqa: S105  # pragma: allowlist secret
        assert saved_data.username == existing_user.username  # Preserved

    @pytest.mark.asyncio
    async def test_handle_with_empty_password_hash(
        self, projection: PasswordChangedProjection
    ) -> None:
        """Test handling with empty password hash."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="emptyuser",
            email="empty@example.com",
            first_name="Empty",
            last_name="User",
            password_hash="old_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        event = PasswordChangedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=PasswordChangedDataV1(
                password_hash="",  # noqa: S106  # pragma: allowlist secret
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.password_hash == ""
        assert saved_data.username == existing_user.username  # Preserved

    @pytest.mark.asyncio
    async def test_handle_with_none_password_hash(
        self, projection: PasswordChangedProjection
    ) -> None:
        """Test handling with None password hash."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="noneuser",
            email="none@example.com",
            first_name="None",
            last_name="User",
            password_hash="old_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        # Note: Pydantic models don't allow None for password_hash, so we'll test with empty string instead
        event = PasswordChangedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=PasswordChangedDataV1(
                password_hash="",  # noqa: S106  # pragma: allowlist secret - empty string instead of None
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.password_hash == ""
        assert saved_data.username == existing_user.username  # Preserved

    @pytest.mark.asyncio
    async def test_handle_with_long_password_hash(
        self, projection: PasswordChangedProjection
    ) -> None:
        """Test handling with long password hash."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="longuser",
            email="long@example.com",
            first_name="Long",
            last_name="User",
            password_hash="old_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        long_hash = "x" * 1000  # pragma: allowlist secret

        event = PasswordChangedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=PasswordChangedDataV1(
                password_hash=long_hash,
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.password_hash == long_hash
        assert saved_data.username == existing_user.username  # Preserved

    @pytest.mark.asyncio
    async def test_handle_with_special_characters_in_password_hash(
        self, projection: PasswordChangedProjection
    ) -> None:
        """Test handling with special characters in password hash."""
        existing_user = UserReadModelData(
            aggregate_id="11111111-1111-1111-1111-111111111111",
            username="specialuser",
            email="special@example.com",
            first_name="Special",
            last_name="User",
            password_hash="old_hash",  # noqa: S106  # pragma: allowlist secret
            created_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc),
        )

        special_hash = (
            "!@#$%^&*()_+-=[]{}|;':\",./<>?"  # pragma: allowlist secret
        )

        event = PasswordChangedV1(
            id=uuid4(),
            aggregate_id=uuid4(),
            event_type=EventType.PASSWORD_CHANGED,
            timestamp=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            version="1",
            revision=1,
            data=PasswordChangedDataV1(
                password_hash=special_hash,
            ),
        )

        projection.read_model.get_user.return_value = existing_user

        await projection.handle(event)

        saved_data = projection.read_model.save_user.call_args[0][0]
        assert saved_data.password_hash == special_hash
        assert saved_data.username == existing_user.username  # Preserved
