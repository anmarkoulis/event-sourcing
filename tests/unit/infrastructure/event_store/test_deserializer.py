"""Unit tests for event deserializer module."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

from event_sourcing.dto.events.user import (
    PasswordChangedDataV1,
    PasswordChangedV1,
    UserCreatedDataV1,
    UserCreatedV1,
    UserDeletedDataV1,
    UserDeletedV1,
    UserUpdatedDataV1,
    UserUpdatedV1,
)
from event_sourcing.enums import EventType, HashingMethod, Role
from event_sourcing.infrastructure.event_store.deserializer import (
    deserialize_event,
    deserialize_event_data,
)


class TestDeserializeEventData:
    """Test cases for deserialize_event_data function."""

    def test_deserialize_user_created_data(self) -> None:
        """Test deserializing USER_CREATED event data."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed_password",  # pragma: allowlist secret
            "hashing_method": "bcrypt",
            "role": "user",
        }

        result = deserialize_event_data(EventType.USER_CREATED, data)

        assert isinstance(result, UserCreatedDataV1)
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert (
            result.password_hash
            == "hashed_password"  # pragma: allowlist secret # noqa: S105
        )
        assert result.hashing_method == HashingMethod.BCRYPT
        assert result.role == Role.USER

    def test_deserialize_user_updated_data(self) -> None:
        """Test deserializing USER_UPDATED event data."""
        data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
        }

        result = deserialize_event_data(EventType.USER_UPDATED, data)

        assert isinstance(result, UserUpdatedDataV1)
        assert result.first_name == "Updated"
        assert result.last_name == "User"
        assert result.email == "updated@example.com"

    def test_deserialize_user_deleted_data(self) -> None:
        """Test deserializing USER_DELETED event data."""
        data: dict[str, str] = {}

        result = deserialize_event_data(EventType.USER_DELETED, data)

        assert isinstance(result, UserDeletedDataV1)

    def test_deserialize_password_changed_data(self) -> None:
        """Test deserializing PASSWORD_CHANGED event data."""
        data = {
            "password_hash": "new_hashed_password",  # pragma: allowlist secret
            "hashing_method": "bcrypt",
        }

        result = deserialize_event_data(EventType.PASSWORD_CHANGED, data)

        assert isinstance(result, PasswordChangedDataV1)
        assert (
            result.password_hash
            == "new_hashed_password"  # pragma: allowlist secret # noqa: S105
        )
        assert result.hashing_method == HashingMethod.BCRYPT

    def test_deserialize_unknown_event_type(self) -> None:
        """Test deserializing unknown event type returns raw data."""
        data = {"custom_field": "custom_value"}

        with patch(
            "event_sourcing.infrastructure.event_store.deserializer.logger"
        ) as mock_logger:
            result = deserialize_event_data("UNKNOWN_EVENT", data)

            # Verify warning was logged
            mock_logger.warning.assert_called_once_with(
                "Unknown event type: UNKNOWN_EVENT, returning raw data"
            )

            # Verify raw data was returned
            assert result == data

    def test_deserialize_with_logging(self) -> None:
        """Test that deserializing logs appropriate messages."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed_password",  # pragma: allowlist secret
            "hashing_method": "bcrypt",
            "role": "user",
        }

        with patch(
            "event_sourcing.infrastructure.event_store.deserializer.logger"
        ) as mock_logger:
            deserialize_event_data(EventType.USER_CREATED, data)

            # Verify debug logging - note that the enum value is converted to string representation
            mock_logger.debug.assert_called_once_with(
                "Deserializing event data for type: EventType.USER_CREATED"
            )


class TestDeserializeEvent:
    """Test cases for deserialize_event function."""

    def test_deserialize_user_created_event(self) -> None:
        """Test deserializing complete USER_CREATED event."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "USER_CREATED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password_hash": "hashed_password",  # pragma: allowlist secret
                "hashing_method": "bcrypt",
                "role": "user",
            },
        }

        result = deserialize_event(event_dict)

        assert isinstance(result, UserCreatedV1)
        assert result.id == event_id
        assert result.aggregate_id == user_id
        assert result.event_type == EventType.USER_CREATED
        assert result.timestamp == datetime(
            2023, 1, 1, 12, 0, tzinfo=timezone.utc
        )
        assert result.version == "1"
        assert result.revision == 1
        assert isinstance(result.data, UserCreatedDataV1)
        assert result.data.username == "testuser"

    def test_deserialize_user_updated_event(self) -> None:
        """Test deserializing complete USER_UPDATED event."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "USER_UPDATED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {
                "first_name": "Updated",
                "last_name": "User",
                "email": "updated@example.com",
            },
        }

        result = deserialize_event(event_dict)

        assert isinstance(result, UserUpdatedV1)
        assert result.id == event_id
        assert result.aggregate_id == user_id
        assert result.event_type == EventType.USER_UPDATED
        assert result.timestamp == datetime(
            2023, 1, 1, 12, 0, tzinfo=timezone.utc
        )
        assert result.version == "1"
        assert result.revision == 1
        assert isinstance(result.data, UserUpdatedDataV1)
        assert result.data.first_name == "Updated"

    def test_deserialize_user_deleted_event(self) -> None:
        """Test deserializing complete USER_DELETED event."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "USER_DELETED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {},
        }

        result = deserialize_event(event_dict)

        assert isinstance(result, UserDeletedV1)
        assert result.id == event_id
        assert result.aggregate_id == user_id
        assert result.event_type == EventType.USER_DELETED
        assert result.timestamp == datetime(
            2023, 1, 1, 12, 0, tzinfo=timezone.utc
        )
        assert result.version == "1"
        assert result.revision == 1
        assert isinstance(result.data, UserDeletedDataV1)

    def test_deserialize_password_changed_event(self) -> None:
        """Test deserializing complete PASSWORD_CHANGED event."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "PASSWORD_CHANGED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {
                "password_hash": "new_hashed_password",  # pragma: allowlist secret
                "hashing_method": "bcrypt",
            },
        }

        result = deserialize_event(event_dict)

        assert isinstance(result, PasswordChangedV1)
        assert result.id == event_id
        assert result.aggregate_id == user_id
        assert result.event_type == EventType.PASSWORD_CHANGED
        assert result.timestamp == datetime(
            2023, 1, 1, 12, 0, tzinfo=timezone.utc
        )
        assert result.version == "1"
        assert result.revision == 1
        assert isinstance(result.data, PasswordChangedDataV1)
        assert (
            result.data.password_hash
            == "new_hashed_password"  # pragma: allowlist secret # noqa: S105
        )

    def test_deserialize_unknown_event_type(self) -> None:
        """Test deserializing unknown event type falls back to generic EventDTO."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "UNKNOWN_EVENT",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {"custom_field": "custom_value"},
        }

        # This should fail because EventType enum doesn't accept unknown values
        with pytest.raises(
            ValueError, match="'UNKNOWN_EVENT' is not a valid EventType"
        ):
            deserialize_event(event_dict)

    def test_deserialize_event_with_minimal_data(self) -> None:
        """Test deserializing event with minimal required data."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "USER_CREATED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password_hash": "hashed_password",  # pragma: allowlist secret
                "hashing_method": "bcrypt",
                "role": "user",
            },
        }

        result = deserialize_event(event_dict)

        assert isinstance(result, UserCreatedV1)
        assert result.id == event_id
        assert result.aggregate_id == user_id
        assert result.event_type == EventType.USER_CREATED
        assert result.timestamp == datetime(
            2023, 1, 1, 12, 0, tzinfo=timezone.utc
        )
        assert result.version == "1"
        assert result.revision == 1
        assert isinstance(result.data, UserCreatedDataV1)

    def test_deserialize_event_with_complex_data(self) -> None:
        """Test deserializing event with complex nested data."""
        event_id = uuid4()
        user_id = uuid4()
        event_dict = {
            "id": str(event_id),
            "aggregate_id": str(user_id),
            "event_type": "USER_CREATED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {
                "username": "complexuser",
                "email": "complex@example.com",
                "first_name": "Complex",
                "last_name": "User",
                "password_hash": "very_long_hashed_password_with_special_chars_!@#$%^&*()",  # pragma: allowlist secret
                "hashing_method": "bcrypt",
                "role": "user",
            },
        }

        result = deserialize_event(event_dict)

        assert isinstance(result, UserCreatedV1)
        assert result.data.username == "complexuser"
        assert result.data.email == "complex@example.com"
        assert result.data.first_name == "Complex"
        assert result.data.last_name == "User"
        assert (
            result.data.password_hash
            == "very_long_hashed_password_with_special_chars_!@#$%^&*()"  # pragma: allowlist secret # noqa: S105
        )
        assert result.data.hashing_method == HashingMethod.BCRYPT
        assert result.data.role == Role.USER

    def test_deserialize_event_with_numeric_strings(self) -> None:
        """Test deserializing event with numeric strings that should be converted."""
        event_dict = {
            "id": str(uuid4()),
            "aggregate_id": str(uuid4()),
            "event_type": "USER_CREATED",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": "1",
            "data": {
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password_hash": "hashed_password",  # pragma: allowlist secret
                "hashing_method": "bcrypt",
                "role": "user",
            },
        }

        result = deserialize_event(event_dict)

        # Verify the event was deserialized correctly
        assert result.id == uuid.UUID(str(event_dict["id"]))
        assert result.aggregate_id == uuid.UUID(
            str(event_dict["aggregate_id"])
        )
        assert result.event_type == EventType.USER_CREATED
        assert result.timestamp == event_dict["timestamp"]
        assert result.version == "1"
        assert result.revision == 1
        assert result.data.username == "testuser"
        assert result.data.email == "test@example.com"

    def test_deserialize_event_data_unknown_event_type(self) -> None:
        """Test deserializing event data for unknown event type."""
        with patch(
            "event_sourcing.infrastructure.event_store.deserializer.logger"
        ) as mock_logger:
            result = deserialize_event_data(
                "UNKNOWN_EVENT_TYPE", {"key": "value"}
            )

            # Should return raw data for unknown event types
            assert result == {"key": "value"}

            # Should log a warning
            mock_logger.warning.assert_called_once_with(
                "Unknown event type: UNKNOWN_EVENT_TYPE, returning raw data"
            )

    def test_deserialize_event_unknown_event_type_raises_error(self) -> None:
        """Test deserializing event with unknown event type raises ValueError."""
        event_dict = {
            "id": str(uuid4()),
            "aggregate_id": str(uuid4()),
            "event_type": "UNKNOWN_EVENT_TYPE",
            "timestamp": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
            "version": "1",
            "revision": 1,
            "data": {"custom_field": "custom_value"},
        }

        # Should raise ValueError for unknown event types
        with pytest.raises(
            ValueError, match="'UNKNOWN_EVENT_TYPE' is not a valid EventType"
        ):
            deserialize_event(event_dict)
