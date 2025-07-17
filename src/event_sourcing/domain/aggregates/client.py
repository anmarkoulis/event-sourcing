import logging
import uuid
from typing import Any, Dict, List, Optional

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.domain.aggregates.salesforce_mixin import (
    SalesforceAggregateMixin,
)
from event_sourcing.dto.event import EventDTO

logger = logging.getLogger(__name__)


class ClientAggregate(Aggregate, SalesforceAggregateMixin):
    """Client domain aggregate - encapsulates client business logic"""

    def __init__(self, aggregate_id: uuid.UUID, provider: Any = None):
        super().__init__(aggregate_id)

        # Store provider for lifecycle management
        self.provider = provider

        # Set aggregate type for Salesforce mixin
        self.aggregate_type = "client"

        # Track events for business logic validation
        self.events: List[EventDTO] = []

        # Client-specific attributes (only what's needed for read model)
        self.name: Optional[str] = None
        self.parent_id: Optional[str] = None
        self.status: Optional[str] = None

    def process_crm_event(
        self,
        crm_event: Dict[str, Any],
        previous_events: List[EventDTO],
        provider_name: str,
    ) -> List[EventDTO]:
        """
        Process a raw CRM event and return domain events.
        This method handles parsing, lifecycle management, and business rules.
        """
        logger.info(
            f"Processing {provider_name} CRM event for aggregate {self.aggregate_id}"
        )

        # Route to provider-specific processing
        if provider_name.lower() == "salesforce":
            return self._process_salesforce_event(crm_event, previous_events)
        else:
            raise ValueError(f"Unsupported CRM provider: {provider_name}")

    def _process_salesforce_event(
        self, salesforce_event: Dict[str, Any], previous_events: List[EventDTO]
    ) -> List[EventDTO]:
        """Process a raw Salesforce event and return domain events"""
        # Parse the Salesforce event using mixin
        parsed_event = self._parse_salesforce_event(salesforce_event)

        # Handle aggregate lifecycle using mixin
        self._handle_salesforce_lifecycle(parsed_event, previous_events)

        # Validate business rules using mixin
        self._validate_salesforce_business_rules(parsed_event, previous_events)

        # Apply business rules and produce domain events
        return self._apply_business_rules(parsed_event)

    def _apply_business_rules(
        self, parsed_event: Dict[str, Any]
    ) -> List[EventDTO]:
        """Apply business rules and produce domain events"""
        # Create the domain event using mixin
        event = self._create_salesforce_domain_event(parsed_event)

        # Apply the event to the aggregate state
        self.apply(event)

        logger.info(
            f"Produced domain event: {event.event_id} of type {event.event_type}"
        )
        return [event]

    def apply(self, event: EventDTO) -> None:
        """Apply a domain event to the client aggregate state"""
        # Track the event for business logic validation
        self.events.append(event)

        if event.event_type.value == "CLIENT_CREATED":
            self._apply_created_event(event)
        elif event.event_type.value == "CLIENT_UPDATED":
            self._apply_updated_event(event)
        elif event.event_type.value == "CLIENT_DELETED":
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    def _apply_created_event(self, event: EventDTO) -> None:
        """Apply client created event"""
        data = event.data
        self.name = data.get("name")
        self.parent_id = data.get("parent_id")
        self.status = data.get("status")

    def _apply_updated_event(self, event: EventDTO) -> None:
        """Apply client updated event"""
        data = event.data
        # Update only provided fields
        if "name" in data:
            self.name = data["name"]
        if "parent_id" in data:
            self.parent_id = data["parent_id"]
        if "status" in data:
            self.status = data["status"]

    def _apply_deleted_event(self, event: EventDTO) -> None:
        """Apply client deleted event"""
        # Mark as deleted (could set a deleted flag or clear fields)
        self.name = None
        self.parent_id = None
        self.status = None
