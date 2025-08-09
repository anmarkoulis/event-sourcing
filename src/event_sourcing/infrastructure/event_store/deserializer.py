import logging
from typing import Any, Dict

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
from event_sourcing.enums import EventType

logger = logging.getLogger(__name__)


def deserialize_event_data(event_type: EventType, data: Dict[str, Any]) -> Any:
    """Deserialize event data based on event type"""
    logger.debug(f"Deserializing event data for type: {event_type}")

    if event_type == EventType.USER_CREATED:
        return UserCreatedDataV1(**data)
    elif event_type == EventType.USER_UPDATED:
        return UserUpdatedDataV1(**data)
    elif event_type == EventType.USER_DELETED:
        return UserDeletedDataV1(**data)
    elif event_type == EventType.PASSWORD_CHANGED:
        return PasswordChangedDataV1(**data)
    else:
        logger.warning(f"Unknown event type: {event_type}, returning raw data")
        return data


def deserialize_event(event_dict: Dict[str, Any]) -> Any:
    """Deserialize a complete event from dictionary"""
    event_type = EventType(event_dict["event_type"])

    if event_type == EventType.USER_CREATED:
        data = UserCreatedDataV1(**event_dict["data"])
        return UserCreatedV1(
            id=event_dict["id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.USER_UPDATED:
        data = UserUpdatedDataV1(**event_dict["data"])
        return UserUpdatedV1(
            id=event_dict["id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.USER_DELETED:
        data = UserDeletedDataV1(**event_dict["data"])
        return UserDeletedV1(
            id=event_dict["id"],
            aggregate_id=event_dict["aggregate_id"],
            timestamp=event_dict["timestamp"],
            version=event_dict["version"],
            revision=event_dict["revision"],
            data=data,
        )
    elif event_type == EventType.PASSWORD_CHANGED:
        data = PasswordChangedDataV1(**event_dict["data"])
        return PasswordChangedV1(
            id=event_dict["id"],
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
