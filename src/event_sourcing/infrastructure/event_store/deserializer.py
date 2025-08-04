from typing import Any, Dict

from event_sourcing.dto.events.user import (
    PasswordChangedV1,
    PasswordResetCompletedV1,
    PasswordResetRequestedV1,
    UserCreatedV1,
    UserDeletedV1,
    UsernameChangedV1,
    UserUpdatedV1,
)
from event_sourcing.dto.events.user.password_changed import (
    PasswordChangedDataV1,
)
from event_sourcing.dto.events.user.password_reset_completed import (
    PasswordResetCompletedDataV1,
)
from event_sourcing.dto.events.user.password_reset_requested import (
    PasswordResetRequestedDataV1,
)
from event_sourcing.dto.events.user.user_created import UserCreatedDataV1
from event_sourcing.dto.events.user.user_deleted import UserDeletedDataV1
from event_sourcing.dto.events.user.user_updated import UserUpdatedDataV1
from event_sourcing.dto.events.user.username_changed import (
    UsernameChangedDataV1,
)
from event_sourcing.enums import EventType


def deserialize_event_data(event_type: EventType, data: Dict[str, Any]) -> Any:
    """Deserialize event data from database dictionary to typed data model"""

    if event_type == EventType.USER_CREATED:
        return UserCreatedDataV1(**data)
    elif event_type == EventType.USER_UPDATED:
        return UserUpdatedDataV1(**data)
    elif event_type == EventType.USER_DELETED:
        return UserDeletedDataV1(**data)
    elif event_type == EventType.USERNAME_CHANGED:
        return UsernameChangedDataV1(**data)
    elif event_type == EventType.PASSWORD_CHANGED:
        return PasswordChangedDataV1(**data)
    elif event_type == EventType.PASSWORD_RESET_REQUESTED:
        return PasswordResetRequestedDataV1(**data)
    elif event_type == EventType.PASSWORD_RESET_COMPLETED:
        return PasswordResetCompletedDataV1(**data)
    else:
        # Fallback to dictionary for unknown event types
        return data


def deserialize_event(event_dict: Dict[str, Any]) -> Any:
    """Deserialize complete event from dictionary to typed event DTO"""

    event_type = EventType(event_dict["event_type"])

    if event_type == EventType.USER_CREATED:
        data = UserCreatedDataV1(**event_dict["data"])
        return UserCreatedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.USER_UPDATED:
        data = UserUpdatedDataV1(**event_dict["data"])
        return UserUpdatedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.USER_DELETED:
        data = UserDeletedDataV1(**event_dict["data"])
        return UserDeletedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.USERNAME_CHANGED:
        data = UsernameChangedDataV1(**event_dict["data"])
        return UsernameChangedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.PASSWORD_CHANGED:
        data = PasswordChangedDataV1(**event_dict["data"])
        return PasswordChangedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.PASSWORD_RESET_REQUESTED:
        data = PasswordResetRequestedDataV1(**event_dict["data"])
        return PasswordResetRequestedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.PASSWORD_RESET_COMPLETED:
        data = PasswordResetCompletedDataV1(**event_dict["data"])
        return PasswordResetCompletedV1(
            event_id=event_dict["event_id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    else:
        # Fallback to generic EventDTO for unknown event types
        from event_sourcing.dto import EventDTO

        return EventDTO(**event_dict)
