import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from event_sourcing.dto.event import EventDTO
from event_sourcing.enums import EventSourceEnum, EventType

logger = logging.getLogger(__name__)


class SalesforceAggregateMixin:
    """Mixin providing Salesforce-specific functionality for aggregates"""

    # These attributes should be defined by the concrete aggregate class
    aggregate_id: uuid.UUID
    aggregate_type: str

    def _parse_salesforce_event(
        self, salesforce_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse raw Salesforce event and extract relevant information"""
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
        external_id = record_ids[0] if record_ids else str(uuid.uuid4())

        # Map Salesforce change type to EventType enum
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
            "salesforce_event_id": salesforce_event.get("id"),
            "aws_source": salesforce_event.get("source"),
            "aws_detail_type": salesforce_event.get("detail-type"),
            "aws_account": salesforce_event.get("account"),
            "aws_region": salesforce_event.get("region"),
            "change_event_header": change_header,
        }

        return {
            "timestamp": timestamp,
            "external_id": external_id,
            "entity_name": entity_name,
            "change_type": change_type,
            "event_type": event_type,
            "payload": payload,
            "event_metadata": event_metadata,
        }

    def _handle_salesforce_lifecycle(
        self,
        parsed_event: Dict[str, Any],
        previous_events: Optional[List[EventDTO]] = None,
    ) -> None:
        """Handle Salesforce-specific aggregate lifecycle"""
        if previous_events is None:
            previous_events = []

        external_id = parsed_event["external_id"]
        change_type = parsed_event["change_type"]

        logger.info(
            f"Handling Salesforce lifecycle for aggregate {self.aggregate_id} with external_id {external_id}"
        )

        # Use previous events to determine if this is a new or existing aggregate
        if previous_events and len(previous_events) > 0:
            logger.info(
                f"Found {len(previous_events)} previous events for external_id {external_id} - treating as UPDATE"
            )
            # In a real implementation, you would reconstruct state here
        else:
            logger.info(
                f"No previous events found for external_id {external_id} - treating as CREATE"
            )

        # Optionally, still use provider for additional checks
        if hasattr(self, "provider") and self.provider:
            try:
                entity_data = self.provider.get_entity(external_id, "Account")
                if entity_data:
                    logger.info(
                        f"Found existing entity {external_id} in Salesforce - treating as UPDATE"
                    )
                else:
                    logger.info(
                        f"Entity {external_id} not found in Salesforce - treating as CREATE"
                    )
            except Exception as e:
                logger.warning(
                    f"Could not check entity existence in Salesforce: {e}"
                )
                if change_type.upper() == "CREATE":
                    logger.info(
                        f"Change type is CREATE - treating as new entity"
                    )
                else:
                    logger.info(
                        f"Change type is {change_type} - treating as existing entity"
                    )
        else:
            logger.warning(
                "No provider available for Salesforce lifecycle management"
            )
            if change_type.upper() == "CREATE":
                logger.info(f"Change type is CREATE - treating as new entity")
            else:
                logger.info(
                    f"Change type is {change_type} - treating as existing entity"
                )

    def _validate_salesforce_business_rules(
        self, parsed_event: Dict[str, Any], previous_events: List[EventDTO]
    ) -> None:
        """Validate Salesforce-specific business rules"""
        change_type = parsed_event["change_type"]
        external_id = parsed_event["external_id"]

        # Business rule: Cannot UPDATE or DELETE before CREATE
        if change_type.upper() in ["UPDATE", "DELETE"]:
            if not previous_events:
                raise ValueError(
                    f"Business rule violation: Cannot {change_type} entity {external_id} "
                    f"before it has been created. No previous events found."
                )

            # Check if the first event was a CREATE
            first_event = previous_events[0]
            if first_event.event_type != EventType.CLIENT_CREATED:
                raise ValueError(
                    f"Business rule violation: Cannot {change_type} entity {external_id} "
                    f"before it has been created. First event was {first_event.event_type}, not CLIENT_CREATED."
                )

            logger.info(
                f"Business rule validation passed: {change_type} operation allowed for entity {external_id}"
            )

    def _create_salesforce_domain_event(
        self, parsed_event: Dict[str, Any]
    ) -> EventDTO:
        """Create a domain event from parsed Salesforce event"""
        return EventDTO(
            event_id=uuid.uuid4(),
            aggregate_id=self.aggregate_id,
            external_id=parsed_event["external_id"],
            aggregate_type=self.aggregate_type,  # This should be set by the concrete aggregate
            event_type=parsed_event["event_type"],
            timestamp=parsed_event["timestamp"],
            version="1.0",
            data=parsed_event["payload"],
            event_metadata=parsed_event["event_metadata"],
            validation_info=None,
            source=EventSourceEnum.SALESFORCE,
            processed_at=parsed_event["timestamp"],
        )
