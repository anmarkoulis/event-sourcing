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
    aggregate_id: str = Field(
        ..., min_length=1, description="Aggregate ID cannot be empty"
    )
    aggregate_type: str = Field(
        ..., min_length=1, description="Aggregate type cannot be empty"
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

    @field_validator("aggregate_id", "aggregate_type", "version")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that string fields are not empty"""
        if not v or not v.strip():
            raise ValueError(f"Field cannot be empty: {v}")
        return v.strip()

    @classmethod
    def from_salesforce_event(
        cls, salesforce_event: Dict[str, Any]
    ) -> "EventDTO":
        """
        Create EventDTO from Salesforce AWS EventBridge payload.
        Extracts relevant information and preserves the full original payload.
        """
        # Generate our own UUID for the event
        event_id = uuid.uuid4()

        # Extract timestamp from Salesforce event
        timestamp_str = salesforce_event.get("time")
        if timestamp_str:
            try:
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str.replace("Z", "+00:00")
                timestamp = datetime.fromisoformat(timestamp_str)
            except Exception:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()

        # Extract ChangeEventHeader for aggregate info
        payload = salesforce_event.get("detail", {}).get("payload", {})
        change_header = payload.get("ChangeEventHeader", {})
        entity_name = change_header.get("entityName", "Account")
        change_type = change_header.get("changeType", "CREATE")
        record_ids = change_header.get("recordIds", [])
        aggregate_id = record_ids[0] if record_ids else str(uuid.uuid4())
        aggregate_type = cls.get_aggregate_type(entity_name)

        # Map Salesforce change type to ALL_CAPS EventType enum
        event_type_map = {
            "CREATE": EventType.CLIENT_CREATED,
            "UPDATE": EventType.CLIENT_UPDATED,
            "DELETE": EventType.CLIENT_DELETED,
        }
        event_type = event_type_map.get(
            change_type.upper(), EventType.CLIENT_UPDATED
        )

        # Compose event metadata with Salesforce ID for reference
        event_metadata = {
            "salesforce_event_id": salesforce_event.get(
                "id"
            ),  # Keep Salesforce ID for reference
            "aws_source": salesforce_event.get("source"),
            "aws_detail_type": salesforce_event.get("detail-type"),
            "aws_account": salesforce_event.get("account"),
            "aws_region": salesforce_event.get("region"),
            "change_event_header": change_header,
        }

        return cls(
            event_id=event_id,  # Our own UUID
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            timestamp=timestamp,
            version="1.0",
            data=payload,  # Store the Salesforce payload (actual record data)
            event_metadata=event_metadata,
            validation_info=None,
            source=EventSourceEnum.SALESFORCE,
            processed_at=timestamp,
        )

    @classmethod
    def get_aggregate_type(cls, entity_name: str) -> str:
        """Get aggregate type from entity name"""
        if entity_name == "Account":
            return "client"
        elif entity_name == "Contact":
            return "contact"
        else:
            raise ValueError(f"Unknown entity name: {entity_name}")
