import uuid
from datetime import datetime
from typing import Any, Dict, List

from pydantic import Field, field_validator

from event_sourcing.enums import EventSourceEnum

from .base import ModelConfigBaseModel
from .event import EventWriteDTO


class SalesforceChangeEventHeader(ModelConfigBaseModel):
    """Salesforce Change Event Header from AWS EventBridge"""

    entityName: str = Field(
        ...,
        description="Salesforce entity name (e.g., Account, Contact, Lead, Opportunity)",
    )
    changeType: str = Field(
        ..., description="Type of change (CREATE, UPDATE, DELETE)"
    )
    recordIds: List[str] = Field(
        ..., description="List of affected record IDs"
    )
    commitTimestamp: str = Field(..., description="Timestamp of the change")


class SalesforceEventDTO(ModelConfigBaseModel):
    """Salesforce-specific DTO for AWS EventBridge events"""

    version: str = Field(..., description="AWS EventBridge version")
    id: str = Field(..., description="AWS EventBridge event ID")
    detail_type: str = Field(
        alias="detail-type", description="AWS EventBridge detail type"
    )
    source: str = Field(..., description="AWS EventBridge source")
    account: str = Field(..., description="AWS account ID")
    time: str = Field(..., description="AWS EventBridge timestamp")
    region: str = Field(..., description="AWS region")
    resources: List[str] = Field(
        default_factory=list, description="AWS EventBridge resources"
    )
    detail: Dict[str, Any] = Field(
        ..., description="AWS EventBridge detail containing Salesforce payload"
    )

    @field_validator("source")
    @classmethod
    def validate_salesforce_source(cls, v: str) -> str:
        """Validate that the source is from Salesforce"""
        if "salesforce.com" not in v:
            raise ValueError("Source must be from Salesforce")
        return v

    @field_validator("detail_type")
    @classmethod
    def validate_detail_type(cls, v: str) -> str:
        """Validate that the detail type is for object record changes"""
        if v != "Object Record Change":
            raise ValueError("Detail type must be 'Object Record Change'")
        return v

    def extract_salesforce_payload(self) -> Dict[str, Any]:
        """Extract the Salesforce payload from the detail"""
        detail: Dict[str, Any] = self.detail
        payload: Dict[str, Any] = detail.get("payload", detail)

        # Validate that we have the required Salesforce structure
        if "ChangeEventHeader" not in payload:
            raise ValueError(
                "Salesforce payload must contain ChangeEventHeader"
            )

        return payload

    def to_event_write_dto(self) -> EventWriteDTO:
        """Convert Salesforce DTO to generic EventWriteDTO"""
        # Parse timestamp
        if self.time.endswith("Z"):
            timestamp_str = self.time.replace("Z", "+00:00")
        else:
            timestamp_str = self.time
        timestamp = datetime.fromisoformat(timestamp_str)

        # Extract aggregate information from ChangeEventHeader
        detail = self.detail
        payload = detail.get("payload", detail)
        change_header = payload.get("ChangeEventHeader", {})
        entity_name = change_header.get("entityName", "Account")
        change_type = change_header.get("changeType", "CREATE")
        record_ids = change_header.get("recordIds", [])

        # Use the first record ID as aggregate_id, or generate one
        aggregate_id = record_ids[0] if record_ids else str(uuid.uuid4())
        aggregate_type = entity_name.lower()
        event_type = change_type.lower()

        # Create event metadata with AWS context
        event_metadata = {
            "aws_event_id": self.id,
            "aws_source": self.source,
            "aws_detail_type": self.detail_type,
            "aws_account": self.account,
            "aws_region": self.region,
            "change_event_header": change_header,
        }

        return EventWriteDTO(
            event_id=uuid.UUID(self.id),
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            timestamp=timestamp,
            version="1.0",
            data=self.model_dump(),  # Full AWS EventBridge event
            event_metadata=event_metadata,
            validation_info=None,
            source=EventSourceEnum.SALESFORCE,
        )
