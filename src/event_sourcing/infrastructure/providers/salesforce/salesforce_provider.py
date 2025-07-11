import logging
from typing import Any, Dict, Optional

from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.domain.events.client import (
    ClientCreatedEvent,
    ClientDeletedEvent,
    ClientUpdatedEvent,
)
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

    def parse_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Salesforce CDC event format to common format"""
        try:
            # Extract the payload from the CDC event structure
            payload = raw_event.get("detail", {}).get("payload", {})
            change_event_header = payload.get("ChangeEventHeader", {})

            entity_name = change_event_header.get("entityName")
            change_type = change_event_header.get("changeType")
            record_ids = change_event_header.get("recordIds", [])

            if not record_ids:
                logger.warning("No record IDs found in ChangeEventHeader")
                return {}

            record_id = record_ids[0]  # Take the first record ID

            return {
                "entity_id": record_id,
                "entity_type": entity_name,
                "change_type": change_type,
                "raw_data": raw_event,
                "metadata": {
                    "source": "salesforce",
                    "entity_name": entity_name,
                    "change_type": change_type,
                    "record_id": record_id,
                    "commit_timestamp": change_event_header.get(
                        "commitTimestamp"
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error parsing Salesforce event: {e}")
            return {}

    def translate_to_domain_event(
        self, parsed_event: Dict[str, Any]
    ) -> DomainEvent:
        """Transform parsed Salesforce event to domain event"""
        entity_id = parsed_event.get("entity_id")
        entity_type = parsed_event.get("entity_type")
        change_type = parsed_event.get("change_type")
        raw_data = parsed_event.get("raw_data", {})
        metadata = parsed_event.get("metadata", {})

        # Validate required fields
        if not entity_id:
            raise ValueError("entity_id is required")
        if not entity_type:
            raise ValueError("entity_type is required")
        if not change_type:
            raise ValueError("change_type is required")

        # Extract the actual Salesforce record data from the CDC event
        # The CDC event contains the record data in the payload
        payload = raw_data.get("detail", {}).get("payload", {})

        # Map Salesforce entity names to our domain entities
        if entity_type == "Account":
            if change_type == "CREATE":
                return ClientCreatedEvent.create(
                    aggregate_id=entity_id,
                    data=payload,  # Use the actual record data, not the full CDC event
                    metadata=metadata,
                )
            elif change_type == "UPDATE":
                return ClientUpdatedEvent.create(
                    aggregate_id=entity_id,
                    data=payload,  # Use the actual record data, not the full CDC event
                    metadata=metadata,
                )
            elif change_type == "DELETE":
                return ClientDeletedEvent.create(
                    aggregate_id=entity_id,
                    data=payload,  # Use the actual record data, not the full CDC event
                    metadata=metadata,
                )
            else:
                raise ValueError(f"Unsupported change type: {change_type}")
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        return "salesforce"
