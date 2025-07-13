import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventSourceEnum, EventType
from event_sourcing.infrastructure.providers.base import CRMProviderInterface

logger = logging.getLogger(__name__)


class SalesforceProvider(CRMProviderInterface):
    """Salesforce CRM provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None  # Will be set by infrastructure factory
        logger.info("Initialized Salesforce provider")

    def set_client(self, client: Any) -> None:
        """Set the Salesforce client (called by infrastructure factory)"""
        self.client = client

    async def get_entity(
        self, entity_id: str, entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch entity from Salesforce"""
        if not self.client:
            logger.warning("Salesforce client not available")
            return None

        try:
            return await self.client.get_entity(entity_id, entity_type)
        except Exception as e:
            logger.error(f"Error fetching entity from Salesforce: {e}")
            return None

    def create_event_dto(self, raw_event: Dict[str, Any]) -> EventDTO:
        """Create EventDTO directly from raw Salesforce CDC event"""
        try:
            # Extract the payload from the CDC event structure
            payload = raw_event.get("detail", {}).get("payload", {})
            change_event_header = payload.get("ChangeEventHeader", {})

            entity_name = change_event_header.get("entityName")
            change_type = change_event_header.get("changeType")
            record_ids = change_event_header.get("recordIds", [])

            if not record_ids:
                raise ValueError("No record IDs found in ChangeEventHeader")

            record_id = record_ids[0]  # Take the first record ID

            # Map Salesforce entity names to our domain aggregate types
            entity_to_aggregate_map = {
                "Account": "client",
                # Add more mappings as needed
                # "Contact": "contact",
                # "Opportunity": "deal",
                # "Contract": "contract",
            }

            aggregate_type = entity_to_aggregate_map.get(entity_name)
            if not aggregate_type:
                raise ValueError(
                    f"Unsupported Salesforce entity type: {entity_name}"
                )

            # Map Salesforce change type to EventType enum
            event_type_map = {
                "CREATE": EventType.CLIENT_CREATED,
                "UPDATE": EventType.CLIENT_UPDATED,
                "DELETE": EventType.CLIENT_DELETED,
            }
            event_type = event_type_map.get(
                change_type.upper(), EventType.CLIENT_UPDATED
            )

            # Extract timestamp from raw event
            timestamp_str = raw_event.get("time")
            if timestamp_str:
                try:
                    if timestamp_str.endswith("Z"):
                        timestamp_str = timestamp_str.replace("Z", "+00:00")
                    timestamp = datetime.fromisoformat(timestamp_str)
                except Exception:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()

            # Create metadata
            metadata = {
                "salesforce_event_id": raw_event.get("id"),
                "aws_source": raw_event.get("source"),
                "aws_detail_type": raw_event.get("detail-type"),
                "aws_account": raw_event.get("account"),
                "aws_region": raw_event.get("region"),
                "change_event_header": change_event_header,
                "salesforce_entity_name": entity_name,  # Keep original entity name for reference
            }

            return EventDTO(
                event_id=uuid.uuid4(),
                aggregate_id=record_id,
                aggregate_type=aggregate_type,  # Use mapped aggregate type
                event_type=event_type,
                timestamp=timestamp,
                version="1.0",
                data=raw_event,  # Keep the full raw event for reference
                event_metadata=metadata,
                validation_info=None,
                source=EventSourceEnum.SALESFORCE,
                processed_at=timestamp,
            )
        except Exception as e:
            logger.error(f"Error creating EventDTO from Salesforce event: {e}")
            raise

    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        return "salesforce"
