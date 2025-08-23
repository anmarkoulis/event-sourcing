import re
import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import Field, field_validator

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

    @field_validator("data")
    @classmethod
    def validate_data_not_none(cls, v: T) -> T:
        """Ensure data is not None."""
        if v is None:
            raise ValueError("Event data cannot be None")
        return v

    @classmethod
    def get_version(cls) -> str:
        """Get the version for this event type.

        Extracts version from class name using patterns like:
        - UserCreatedV1 -> "1"
        - UserCreatedV2 -> "2"
        - UserCreatedv1 -> "1"
        - UserCreatedv2 -> "2"
        - UserCreated -> "1" (default)
        """
        class_name = cls.__name__

        # Pattern to match V1, V2, V3... or v1, v2, v3... at the end of class name
        version_pattern = r"[Vv](\d+)$"
        match = re.search(version_pattern, class_name)

        if match:
            return match.group(1)  # Return the captured version number

        # Default version if no pattern matches
        return "1"
