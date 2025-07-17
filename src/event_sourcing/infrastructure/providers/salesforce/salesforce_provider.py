import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventSourceEnum, EventType
from event_sourcing.infrastructure.providers.base.provider_interface import (
    CRMProviderInterface,
)

logger = logging.getLogger(__name__)


class SalesforceProvider(CRMProviderInterface):
    """Salesforce CRM provider implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Salesforce provider initialized")

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

            # Generate UUID for aggregate_id and use Salesforce record_id as external_id
            aggregate_id = uuid.uuid4()
            external_id = record_id

            # Create event metadata with AWS context
            event_metadata = {
                "aws_event_id": raw_event.get("id"),
                "aws_source": raw_event.get("source"),
                "aws_detail_type": raw_event.get("detail-type"),
                "aws_account": raw_event.get("account"),
                "aws_region": raw_event.get("region"),
                "change_event_header": change_event_header,
            }

            return EventDTO(
                event_id=uuid.uuid4(),
                aggregate_id=aggregate_id,
                external_id=external_id,
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

        except Exception as e:
            logger.error(f"Error creating EventDTO from Salesforce event: {e}")
            raise

    def extract_identifiers(self, raw_event: dict) -> tuple[str, str]:
        """Extract external_id and source from raw Salesforce event"""
        payload = raw_event.get("detail", {}).get("payload", {})
        change_event_header = payload.get("ChangeEventHeader", {})
        record_ids = change_event_header.get("recordIds", [])
        external_id = record_ids[0] if record_ids else str(uuid.uuid4())
        source = "SALESFORCE"
        return external_id, source

    def extract_aggregate_type(self, raw_event: dict) -> str:
        """Extract aggregate type from raw Salesforce event"""
        payload = raw_event.get("detail", {}).get("payload", {})
        change_event_header = payload.get("ChangeEventHeader", {})
        entity_name = change_event_header.get("entityName")

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

        return aggregate_type

    def get_entity(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """Get entity from Salesforce (for backfill scenarios)"""
        # This would make actual Salesforce API calls
        # For now, return mock data
        logger.info(f"Getting {entity_type} {entity_id} from Salesforce")
        return {
            "id": entity_id,
            "name": f"Mock {entity_type} {entity_id}",
            "status": "Active",
            "created_at": "2024-01-01T00:00:00Z",
        }

    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        return "salesforce"
