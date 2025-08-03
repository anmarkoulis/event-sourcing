import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field, field_validator

from event_sourcing.enums import EventSourceEnum, EventType

from .base import ModelConfigBaseModel


class EventDTO(ModelConfigBaseModel):
    """Single Event DTO for all event operations"""

    event_id: uuid.UUID = Field(
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
        ..., min_length=1, description="Version cannot be empty"
    )
    data: Dict[str, Any] = Field(..., description="Event data cannot be empty")
    event_metadata: Optional[Dict[str, Any]] = None
    validation_info: Optional[Dict[str, Any]] = None
    source: EventSourceEnum = Field(
        ..., description="Event source must be a valid provider"
    )
    processed_at: Optional[datetime] = None

    @field_validator("version")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that string fields are not empty"""
        if not v or not v.strip():
            raise ValueError(f"Field cannot be empty: {v}")
        return v.strip()
