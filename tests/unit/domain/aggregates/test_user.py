"""Unit tests for UserAggregate domain aggregate."""

import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from event_sourcing.domain.aggregates.user import UserAggregate
from event_sourcing.dto import EventDTO, EventFactory
from event_sourcing.enums import EventType, HashingMethod
from event_sourcing.exceptions import (
    InvalidEmailFormatError,
    PasswordMustBeDifferentError,
    PasswordRequiredError,
    UsernameTooShortError,
    UserNotFoundError,
)


class TestUserAggregate:
    """Test cases for UserAggregate domain aggregate."""

    @pytest.fixture
    def aggregate_id(self) -> uuid.UUID:
        """Provide a test aggregate ID."""
        return uuid.uuid4()

    @pytest.fixture
    def user_aggregate(self, aggregate_id: uuid.UUID) -> UserAggregate:
        """Provide a fresh UserAggregate instance."""
        return UserAggregate(aggregate_id)

    @pytest.fixture
    def valid_user_data(self) -> dict:
        """Provide valid user creation data."""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed_password_123",  # noqa: S106  # pragma: allowlist secret
            "hashing_method": HashingMethod.BCRYPT,
        }

    @pytest.fixture
    def timestamp(self) -> datetime:
        """Provide a fixed timestamp for testing."""
        return datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_init(self, aggregate_id: uuid.UUID) -> None:
        """Test UserAggregate initialization."""
        user = UserAggregate(aggregate_id)

        assert user.aggregate_id == aggregate_id
        assert user.last_applied_revision == 0
        assert user.events == []
        assert user.username is None
        assert user.email is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.password_hash is None
        assert user.created_at is None
        assert user.updated_at is None
        assert user.deleted_at is None

    def test_revision_increments_on_user_creation(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test that revision increments correctly when creating a user."""
        # Initial revision should be 0
        assert user_aggregate.last_applied_revision == 0

        # Create user - this should increment revision to 1
        events = user_aggregate.create_user(**valid_user_data)
        assert len(events) == 1
        assert user_aggregate.last_applied_revision == 1

        # Create another user with same aggregate (should fail, but revision logic is tested)
        user_aggregate.last_applied_revision = 5
        # The next operation would use revision 6, but we can't test it directly
        # without calling private methods. Instead, we test the behavior through
        # the public interface by checking that revisions increment correctly
        assert user_aggregate.last_applied_revision == 5

    def test_snapshot_serialization_deserialization(self) -> None:
        """Test snapshot serialization and deserialization through public methods."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create a user aggregate and populate it with data
        user = UserAggregate(uuid.uuid4())
        user.username = "testuser"
        user.email = "test@example.com"
        user.first_name = "Test"
        user.last_name = "User"
        user.created_at = test_datetime
        user.updated_at = test_datetime
        user.last_applied_revision = 1

        # Test serialization through to_snapshot
        data, revision = user.to_snapshot()
        assert revision == 1
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["created_at"] == "2023-01-01T12:00:00+00:00"
        assert data["updated_at"] == "2023-01-01T12:00:00+00:00"

        # Test deserialization through from_snapshot
        restored_user = UserAggregate.from_snapshot(
            user.aggregate_id, data, revision
        )
        assert restored_user.username == "testuser"
        assert restored_user.email == "test@example.com"
        assert restored_user.created_at == test_datetime
        assert restored_user.updated_at == test_datetime
        assert restored_user.last_applied_revision == 1

        # Test None values are handled correctly
        user_with_none = UserAggregate(uuid.uuid4())
        user_with_none.last_applied_revision = 0
        data_none, revision_none = user_with_none.to_snapshot()
        assert data_none["created_at"] is None
        assert data_none["updated_at"] is None

        # Test from_snapshot with None values
        restored_none_user = UserAggregate.from_snapshot(
            user_with_none.aggregate_id, data_none, revision_none
        )
        assert restored_none_user.created_at is None

        # Test from_snapshot with invalid datetime string
        invalid_data = data.copy()
        invalid_data["created_at"] = "invalid"
        restored_invalid_user = UserAggregate.from_snapshot(
            user.aggregate_id, invalid_data, revision
        )
        assert restored_invalid_user.created_at is None

    def test_create_user_success(
        self,
        user_aggregate: UserAggregate,
        valid_user_data: dict,
        timestamp: datetime,
    ) -> None:
        """Test successful user creation."""
        events = user_aggregate.create_user(
            username=valid_user_data["username"],
            email=valid_user_data["email"],
            first_name=valid_user_data["first_name"],
            last_name=valid_user_data["last_name"],
            password_hash=valid_user_data["password_hash"],
            hashing_method=valid_user_data["hashing_method"],
        )

        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.USER_CREATED
        assert event.aggregate_id == user_aggregate.aggregate_id
        assert event.revision == 1
        assert event.data.username == valid_user_data["username"]
        assert event.data.email == valid_user_data["email"]
        assert event.data.first_name == valid_user_data["first_name"]
        assert event.data.last_name == valid_user_data["last_name"]
        assert event.data.password_hash == valid_user_data["password_hash"]

        # Verify aggregate state was updated
        assert user_aggregate.username == valid_user_data["username"]
        assert user_aggregate.email == valid_user_data["email"]
        assert user_aggregate.first_name == valid_user_data["first_name"]
        assert user_aggregate.last_name == valid_user_data["last_name"]
        assert user_aggregate.password_hash == valid_user_data["password_hash"]
        assert user_aggregate.created_at == event.timestamp
        assert user_aggregate.updated_at == event.timestamp
        assert user_aggregate.last_applied_revision == 1

    def test_create_user_already_exists(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user creation fails when user already exists."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Try to create another user with same aggregate
        from event_sourcing.exceptions import UserAlreadyExistsError

        with pytest.raises(
            UserAlreadyExistsError, match="User 'testuser' already exists"
        ):
            user_aggregate.create_user(**valid_user_data)

    def test_create_user_invalid_username_short(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user creation fails with short username."""
        invalid_data = valid_user_data.copy()
        invalid_data["username"] = "ab"  # Less than 3 characters

        with pytest.raises(UsernameTooShortError):
            user_aggregate.create_user(**invalid_data)

    def test_create_user_invalid_username_empty(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user creation fails with empty username."""
        invalid_data = valid_user_data.copy()
        invalid_data["username"] = ""

        with pytest.raises(UsernameTooShortError):
            user_aggregate.create_user(**invalid_data)

    def test_create_user_invalid_email_no_at(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user creation fails with invalid email format."""
        invalid_data = valid_user_data.copy()
        invalid_data["email"] = "invalid-email"

        with pytest.raises(InvalidEmailFormatError):
            user_aggregate.create_user(**invalid_data)

    def test_create_user_invalid_email_empty(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user creation fails with empty email."""
        invalid_data = valid_user_data.copy()
        invalid_data["email"] = ""

        with pytest.raises(InvalidEmailFormatError):
            user_aggregate.create_user(**invalid_data)

    def test_create_user_no_password(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user creation fails without password."""
        invalid_data = valid_user_data.copy()
        invalid_data["password_hash"] = ""

        with pytest.raises(PasswordRequiredError):
            user_aggregate.create_user(**invalid_data)

    def test_update_user_success(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test successful user update."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Update user information
        events = user_aggregate.update_user(
            first_name="Updated", last_name="Name", email="updated@example.com"
        )

        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.USER_UPDATED
        assert event.revision == 2
        assert event.data.first_name == "Updated"
        assert event.data.last_name == "Name"
        assert event.data.email == "updated@example.com"

        # Verify aggregate state was updated
        assert user_aggregate.first_name == "Updated"
        assert user_aggregate.last_name == "Name"
        assert user_aggregate.email == "updated@example.com"
        assert user_aggregate.last_applied_revision == 2

    def test_update_user_partial(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test partial user update."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Update only first name
        events = user_aggregate.update_user(first_name="Partial")

        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.USER_UPDATED
        assert event.data.first_name == "Partial"
        assert event.data.last_name is None
        assert event.data.email is None

        # Verify only first name was updated
        assert user_aggregate.first_name == "Partial"
        assert user_aggregate.last_name == valid_user_data["last_name"]
        assert user_aggregate.email == valid_user_data["email"]

    def test_update_user_no_fields(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user update fails when no fields provided."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        from event_sourcing.exceptions import NoFieldsToUpdateError

        with pytest.raises(
            NoFieldsToUpdateError, match="No fields provided for update"
        ):
            user_aggregate.update_user()

    def test_update_user_invalid_email(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user update fails with invalid email."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        from event_sourcing.exceptions import InvalidEmailFormatError

        with pytest.raises(InvalidEmailFormatError, match="invalid-email"):
            user_aggregate.update_user(email="invalid-email")

    def test_update_user_deleted_user(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user update fails for deleted user."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Delete the user
        user_aggregate.delete_user()

        # Try to update deleted user
        from event_sourcing.exceptions import (
            CannotUpdateDeletedUserError,
        )

        with pytest.raises(
            CannotUpdateDeletedUserError, match="Cannot update deleted user:"
        ):
            user_aggregate.update_user(first_name="Updated")

    def test_change_password_success(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test successful password change."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Change password
        new_password = "new_hashed_password"  # noqa: S105  # pragma: allowlist secret
        events = user_aggregate.change_password(
            new_password, HashingMethod.BCRYPT
        )

        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.PASSWORD_CHANGED
        assert event.revision == 2
        assert event.data.password_hash == new_password

        # Verify password was updated
        assert user_aggregate.password_hash == new_password
        assert user_aggregate.last_applied_revision == 2

    def test_change_password_no_password(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test password change fails without password."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        from event_sourcing.exceptions import NewPasswordRequiredError

        with pytest.raises(
            NewPasswordRequiredError, match="New password is required"
        ):
            user_aggregate.change_password("", HashingMethod.BCRYPT)

    def test_change_password_deleted_user(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test password change fails for deleted user."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Delete the user
        user_aggregate.delete_user()

        # Try to change password
        from event_sourcing.exceptions import (
            CannotChangePasswordForDeletedUserError,
        )

        with pytest.raises(
            CannotChangePasswordForDeletedUserError,
            match="Cannot change password for deleted user:",
        ):
            user_aggregate.change_password(
                "new_password", HashingMethod.BCRYPT
            )

    def test_change_password_same_password(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test password change fails when new password is same as current."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)
        current_password = valid_user_data["password_hash"]

        # Try to change to the same password
        with pytest.raises(
            PasswordMustBeDifferentError,
            match="New password must be different from current password",
        ):
            user_aggregate.change_password(
                current_password, HashingMethod.BCRYPT
            )

    def test_update_user_not_exists(
        self, user_aggregate: UserAggregate
    ) -> None:
        """Test user update fails when user doesn't exist."""
        # Try to update a user that hasn't been created
        with pytest.raises(
            UserNotFoundError,
            match=f"User {user_aggregate.aggregate_id} not found",
        ):
            user_aggregate.update_user(first_name="Updated")

    def test_change_password_not_exists(
        self, user_aggregate: UserAggregate
    ) -> None:
        """Test password change fails when user doesn't exist."""
        # Try to change password for a user that hasn't been created
        with pytest.raises(
            UserNotFoundError,
            match=f"User {user_aggregate.aggregate_id} not found",
        ):
            user_aggregate.change_password(
                "new_password", HashingMethod.BCRYPT
            )

    def test_delete_user_not_exists(
        self, user_aggregate: UserAggregate
    ) -> None:
        """Test user deletion fails when user doesn't exist."""
        # Try to delete a user that hasn't been created
        with pytest.raises(
            UserNotFoundError,
            match=f"User {user_aggregate.aggregate_id} not found",
        ):
            user_aggregate.delete_user()

    def test_delete_user_success(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test successful user deletion."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Delete the user
        events = user_aggregate.delete_user()

        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.USER_DELETED
        assert event.revision == 2

        # Verify user was marked as deleted
        assert user_aggregate.deleted_at == event.timestamp
        assert user_aggregate.last_applied_revision == 2

    def test_delete_user_already_deleted(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test user deletion fails when already deleted."""
        # First create a user
        user_aggregate.create_user(**valid_user_data)

        # Delete the user
        user_aggregate.delete_user()

        # Try to delete again
        from event_sourcing.exceptions import UserAlreadyDeletedError

        with pytest.raises(
            UserAlreadyDeletedError, match="User .* is already deleted"
        ):
            user_aggregate.delete_user()

    def test_apply_user_created_event(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying USER_CREATED event."""
        event = EventFactory.create_user_created(
            aggregate_id=aggregate_id,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=1,
            timestamp=timestamp,
        )

        user_aggregate.apply(event)

        # Verify event was tracked
        assert len(user_aggregate.events) == 1
        assert user_aggregate.events[0] == event

        # Verify revision was updated
        assert user_aggregate.last_applied_revision == 1

        # Verify aggregate state was updated
        assert user_aggregate.username == "testuser"
        assert user_aggregate.email == "test@example.com"
        assert user_aggregate.first_name == "Test"
        assert user_aggregate.last_name == "User"
        assert user_aggregate.password_hash == "hashed_password"  # noqa: S105  # pragma: allowlist secret
        assert user_aggregate.created_at == timestamp
        assert user_aggregate.updated_at == timestamp

    def test_apply_user_updated_event(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying USER_UPDATED event."""
        # First create a user
        user_aggregate.username = "existing_user"
        user_aggregate.first_name = "Existing"
        user_aggregate.last_name = "User"
        user_aggregate.email = "existing@example.com"
        user_aggregate.last_applied_revision = 1

        event = EventFactory.create_user_updated(
            aggregate_id=aggregate_id,
            first_name="Updated",
            last_name="Name",
            email="updated@example.com",
            revision=2,
            timestamp=timestamp,
        )

        user_aggregate.apply(event)

        # Verify event was tracked
        assert len(user_aggregate.events) == 1
        assert user_aggregate.events[0] == event

        # Verify revision was updated
        assert user_aggregate.last_applied_revision == 2

        # Verify aggregate state was updated
        assert user_aggregate.first_name == "Updated"
        assert user_aggregate.last_name == "Name"
        assert user_aggregate.email == "updated@example.com"
        assert user_aggregate.updated_at == timestamp

    def test_apply_user_updated_event_partial(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying USER_UPDATED event with partial data."""
        # First create a user
        user_aggregate.username = "existing_user"
        user_aggregate.first_name = "Existing"
        user_aggregate.last_name = "User"
        user_aggregate.email = "existing@example.com"
        user_aggregate.last_applied_revision = 1

        event = EventFactory.create_user_updated(
            aggregate_id=aggregate_id,
            first_name="Updated",
            revision=2,
            timestamp=timestamp,
        )

        user_aggregate.apply(event)

        # Verify only first name was updated
        assert user_aggregate.first_name == "Updated"
        assert user_aggregate.last_name == "User"  # Unchanged
        assert user_aggregate.email == "existing@example.com"  # Unchanged
        assert user_aggregate.updated_at == timestamp

    def test_apply_password_changed_event(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying PASSWORD_CHANGED event."""
        # First create a user
        user_aggregate.username = "existing_user"
        user_aggregate.password_hash = "old_password"  # noqa: S105  # pragma: allowlist secret
        user_aggregate.last_applied_revision = 1

        event = EventFactory.create_password_changed(
            aggregate_id=aggregate_id,
            password_hash="new_password",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=2,
            timestamp=timestamp,
        )

        user_aggregate.apply(event)

        # Verify event was tracked
        assert len(user_aggregate.events) == 1
        assert user_aggregate.events[0] == event

        # Verify revision was updated
        assert user_aggregate.last_applied_revision == 2

        # Verify password was updated
        assert user_aggregate.password_hash == "new_password"  # noqa: S105  # pragma: allowlist secret
        assert user_aggregate.updated_at == timestamp

    def test_apply_user_deleted_event(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying USER_DELETED event."""
        # First create a user
        user_aggregate.username = "existing_user"
        user_aggregate.last_applied_revision = 1

        event = EventFactory.create_user_deleted(
            aggregate_id=aggregate_id,
            revision=2,
            timestamp=timestamp,
        )

        user_aggregate.apply(event)

        # Verify event was tracked
        assert len(user_aggregate.events) == 1
        assert user_aggregate.events[0] == event

        # Verify revision was updated
        assert user_aggregate.last_applied_revision == 2

        # Verify user was marked as deleted
        assert user_aggregate.deleted_at == timestamp
        assert user_aggregate.updated_at == timestamp

    def test_apply_unknown_event_type(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying unknown event type."""
        # Create a mock event with unknown type
        mock_event = Mock(spec=EventDTO)
        mock_event.event_type = "UNKNOWN_EVENT"
        mock_event.revision = 1
        mock_event.timestamp = timestamp
        mock_event.data = Mock()

        user_aggregate.apply(mock_event)

        # Verify event was still tracked
        assert len(user_aggregate.events) == 1
        assert user_aggregate.events[0] == mock_event

        # Verify revision was updated
        assert user_aggregate.last_applied_revision == 1

    def test_apply_event_with_none_revision(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test applying event with None revision."""
        event = EventFactory.create_user_created(
            aggregate_id=aggregate_id,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=1,
            timestamp=timestamp,
        )

        # Set revision to None
        event.revision = None

        user_aggregate.apply(event)

        # Verify event was tracked
        assert len(user_aggregate.events) == 1
        assert user_aggregate.events[0] == event

        # Verify revision was not updated
        assert user_aggregate.last_applied_revision == 0

    def test_apply_multiple_events_revision_tracking(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test revision tracking with multiple events."""
        # Create and apply first event
        event1 = EventFactory.create_user_created(
            aggregate_id=aggregate_id,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=1,
            timestamp=timestamp,
        )
        user_aggregate.apply(event1)
        assert user_aggregate.last_applied_revision == 1

        # Create and apply second event
        event2 = EventFactory.create_user_updated(
            aggregate_id=aggregate_id,
            first_name="Updated",
            revision=3,  # Skip revision 2
            timestamp=timestamp,
        )
        user_aggregate.apply(event2)
        assert user_aggregate.last_applied_revision == 3

        # Create and apply third event with lower revision
        event3 = EventFactory.create_password_changed(
            aggregate_id=aggregate_id,
            password_hash="new_password",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=2,  # Lower revision
            timestamp=timestamp,
        )
        user_aggregate.apply(event3)
        assert (
            user_aggregate.last_applied_revision == 3
        )  # Should remain at highest

    def test_from_snapshot(self, aggregate_id: uuid.UUID) -> None:
        """Test creating aggregate from snapshot."""
        snapshot_data = {
            "username": "snapshot_user",
            "email": "snapshot@example.com",
            "first_name": "Snapshot",
            "last_name": "User",
            "password_hash": "snapshot_password",  # noqa: S106  # pragma: allowlist secret
            "created_at": "2023-01-01T12:00:00+00:00",
            "updated_at": "2023-01-02T12:00:00+00:00",
            "deleted_at": None,
        }
        revision = 5

        user = UserAggregate.from_snapshot(
            aggregate_id, snapshot_data, revision
        )

        assert user.aggregate_id == aggregate_id
        assert user.username == "snapshot_user"
        assert user.email == "snapshot@example.com"
        assert user.first_name == "Snapshot"
        assert user.last_name == "User"
        assert user.password_hash == "snapshot_password"  # noqa: S105 # pragma: allowlist secret
        assert user.created_at == datetime(
            2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )
        assert user.updated_at == datetime(
            2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc
        )
        assert user.deleted_at is None
        assert user.last_applied_revision == 5

    def test_from_snapshot_with_none_values(
        self, aggregate_id: uuid.UUID
    ) -> None:
        """Test creating aggregate from snapshot with None values."""
        snapshot_data = {
            "username": None,
            "email": None,
            "first_name": None,
            "last_name": None,
            "password_hash": None,
            "created_at": None,
            "updated_at": None,
            "deleted_at": None,
        }
        revision = 1

        user = UserAggregate.from_snapshot(
            aggregate_id, snapshot_data, revision
        )

        assert user.username is None
        assert user.email is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.password_hash is None
        assert user.created_at is None
        assert user.updated_at is None
        assert user.deleted_at is None

    def test_from_snapshot_invalid_datetime(
        self, aggregate_id: uuid.UUID
    ) -> None:
        """Test creating aggregate from snapshot with invalid datetime."""
        snapshot_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "password",  # noqa: S106  # pragma: allowlist secret
            "created_at": "invalid-datetime",
            "updated_at": "2023-01-01T12:00:00+00:00",
            "deleted_at": None,
        }
        revision = 1

        user = UserAggregate.from_snapshot(
            aggregate_id, snapshot_data, revision
        )

        # Invalid datetime should be parsed as None
        assert user.created_at is None
        assert user.updated_at == datetime(
            2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )

    def test_to_snapshot(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test creating snapshot from aggregate."""
        # Create a user first
        user_aggregate.create_user(**valid_user_data)

        # Create snapshot
        data, revision = user_aggregate.to_snapshot()

        assert revision == 1
        assert data["username"] == valid_user_data["username"]
        assert data["email"] == valid_user_data["email"]
        assert data["first_name"] == valid_user_data["first_name"]
        assert data["last_name"] == valid_user_data["last_name"]
        assert data["password_hash"] == valid_user_data["password_hash"]
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        assert data["deleted_at"] is None

    def test_to_snapshot_with_none_values(
        self, user_aggregate: UserAggregate
    ) -> None:
        """Test creating snapshot with None values."""
        # Create snapshot without creating user
        data, revision = user_aggregate.to_snapshot()

        assert revision == 0
        assert data["username"] is None
        assert data["email"] is None
        assert data["first_name"] is None
        assert data["last_name"] is None
        assert data["password_hash"] is None
        assert data["created_at"] is None
        assert data["updated_at"] is None
        assert data["deleted_at"] is None

    def test_business_methods_integration(
        self, user_aggregate: UserAggregate, valid_user_data: dict
    ) -> None:
        """Test integration of all business methods working together."""
        # Create user
        create_events = user_aggregate.create_user(**valid_user_data)
        assert len(create_events) == 1
        assert user_aggregate.username == valid_user_data["username"]
        assert user_aggregate.last_applied_revision == 1

        # Update user
        update_events = user_aggregate.update_user(first_name="Updated")
        assert len(update_events) == 1
        assert user_aggregate.first_name == "Updated"
        assert user_aggregate.last_applied_revision == 2

        # Change password
        password_events = user_aggregate.change_password(
            "new_password", HashingMethod.BCRYPT
        )
        assert len(password_events) == 1
        assert user_aggregate.password_hash == "new_password"  # noqa: S105  # pragma: allowlist secret
        assert user_aggregate.last_applied_revision == 3

        # Delete user
        delete_events = user_aggregate.delete_user()
        assert len(delete_events) == 1
        assert user_aggregate.deleted_at is not None
        assert user_aggregate.last_applied_revision == 4

        # Verify all events were tracked
        assert len(user_aggregate.events) == 4
        assert user_aggregate.events[0].event_type == EventType.USER_CREATED
        assert user_aggregate.events[1].event_type == EventType.USER_UPDATED
        assert (
            user_aggregate.events[2].event_type == EventType.PASSWORD_CHANGED
        )
        assert user_aggregate.events[3].event_type == EventType.USER_DELETED

    def test_event_application_order(
        self,
        user_aggregate: UserAggregate,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
    ) -> None:
        """Test that events are applied in the correct order."""
        # Create events out of order
        event3 = EventFactory.create_password_changed(
            aggregate_id=aggregate_id,
            password_hash="password3",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=3,
            timestamp=timestamp,
        )
        event1 = EventFactory.create_user_created(
            aggregate_id=aggregate_id,
            username="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            password_hash="password1",  # noqa: S106  # pragma: allowlist secret
            hashing_method=HashingMethod.BCRYPT,
            revision=1,
            timestamp=timestamp,
        )
        event2 = EventFactory.create_user_updated(
            aggregate_id=aggregate_id,
            first_name="Updated",
            revision=2,
            timestamp=timestamp,
        )

        # Apply events in order
        user_aggregate.apply(event1)
        user_aggregate.apply(event2)
        user_aggregate.apply(event3)

        # Verify final state
        assert user_aggregate.username == "user1"
        assert user_aggregate.first_name == "Updated"
        assert user_aggregate.password_hash == "password3"  # noqa: S105  # pragma: allowlist secret
        assert user_aggregate.last_applied_revision == 3
        assert len(user_aggregate.events) == 3
