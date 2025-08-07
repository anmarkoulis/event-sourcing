import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import Field

from event_sourcing.dto.base import ModelConfigBaseModel
from event_sourcing.enums import EventType

# Type variable for event data
T = TypeVar("T")


class EventDTO(ModelConfigBaseModel, Generic[T]):
    """Base Event DTO with type-safe data field"""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Event ID - required UUID"
    )
    aggregate_id: uuid.UUID = Field(
        ...,
        description="Internal aggregate ID - UUID",
    )
    event_type: EventType = Field(
        ..., description="Event type using EventType enum"
    )
    timestamp: datetime
    version: str = Field(
        ..., min_length=1, description="Schema version of the event"
    )
    revision: int = Field(
        ...,
        ge=1,
        description="Sequence number/order of the event in the aggregate stream",
    )
    data: T = Field(..., description="Type-safe event data")

    @classmethod
    def get_version(cls) -> str:
        """Get the version for this event type"""
        # Extract version from class name (e.g., UserCreatedV1 -> "1")
        class_name = cls.__name__
        if class_name.endswith("V1"):
            return "1"
        # Add more version patterns as needed
        return "1"  # Default version
