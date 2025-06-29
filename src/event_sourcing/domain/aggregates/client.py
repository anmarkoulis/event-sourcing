import logging
from datetime import datetime
from typing import Any, List, Optional

from event_sourcing.domain.aggregates.salesforce import SalesforceAggregate
from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.domain.events.client import (
    ClientCreatedEvent,
    ClientDeletedEvent,
    ClientUpdatedEvent,
)

logger = logging.getLogger(__name__)


class ClientAggregate(SalesforceAggregate):
    """Client domain aggregate - encapsulates client business logic"""

    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id, "Account")

        # Track events for business logic validation
        self.events: List[DomainEvent] = []

        # Client-specific attributes (only what's needed for read model)
        self.name: Optional[str] = None
        self.parent_id: Optional[str] = None
        self.status: Optional[str] = None

    def process_salesforce_event(
        self,
        salesforce_event: DomainEvent,
        salesforce_client: Optional[Any] = None,
    ) -> List[DomainEvent]:
        """
        Process Salesforce event with business logic.

        Business Rules:
        1. If UPDATE received before CREATE, fetch complete state and create CREATE event
        2. Only broadcast events for active clients (status != 'Inactive')
        """
        logger.info(
            f"Processing Salesforce event: {salesforce_event.event_type} for client {self.aggregate_id}"
        )

        # Business Rule 1: Handle missing CREATE events
        if (
            salesforce_event.event_type == "Updated"
            and not self.events
            and salesforce_event.metadata.get("source") == "salesforce"
        ):
            logger.info(
                f"UPDATE received before CREATE for client {self.aggregate_id}, fetching complete state"
            )
            return self._handle_missing_create_event(
                salesforce_event, salesforce_client
            )

        # Business Rule 2: Validate event sequence
        if not self._is_valid_event_sequence(salesforce_event):
            raise ValueError(
                f"Invalid event sequence: {salesforce_event.event_type} for client {self.aggregate_id}"
            )

        # Transform Salesforce event to domain event
        domain_event = self._transform_to_domain_event(salesforce_event)

        # Business Rule 3: Check if event should be broadcasted
        if not self._should_broadcast_event(domain_event):
            logger.info(
                f"Event for client {self.aggregate_id} will not be broadcasted (inactive client)"
            )
            # Still return the event for storage, but mark it as non-broadcastable
            domain_event.metadata["broadcast"] = False
        else:
            domain_event.metadata["broadcast"] = True

        return [domain_event]

    def _handle_missing_create_event(
        self, salesforce_event: DomainEvent, salesforce_client: Optional[Any]
    ) -> List[DomainEvent]:
        """Business logic: Handle missing CREATE event by fetching complete state"""
        if not salesforce_client:
            raise ValueError(
                "Salesforce client required to handle missing CREATE event"
            )

        try:
            # Fetch complete entity state from Salesforce
            complete_state = salesforce_client.get_entity(
                self.aggregate_id, self.entity_name
            )

            if not complete_state:
                raise ValueError(
                    f"Entity not found in Salesforce: {self.aggregate_id}"
                )

            # Create a CREATE event from the complete state
            create_event = ClientCreatedEvent.create(
                aggregate_id=self.aggregate_id,
                data=complete_state,
                metadata={
                    **salesforce_event.metadata,
                    "source": "salesforce_api_fetch",  # Mark as API-fetched
                    "original_event_type": "Updated",  # Track original event
                    "reason": "missing_create_event",
                },
            )

            logger.info(
                f"Created CREATE event from API response for client {self.aggregate_id}"
            )
            return [create_event]

        except Exception as e:
            logger.error(
                f"Error fetching complete state for client {self.aggregate_id}: {e}"
            )
            raise

    def _is_valid_event_sequence(self, event: DomainEvent) -> bool:
        """Business logic: Validate event ordering"""
        if event.event_type == "Created" and self.events:
            logger.warning(
                f"CREATE event received for existing client {self.aggregate_id}"
            )
            return False

        if event.event_type != "Created" and not self.events:
            # This is handled by _handle_missing_create_event
            return True

        return True

    def _transform_to_domain_event(
        self, salesforce_event: DomainEvent
    ) -> DomainEvent:
        """Transform Salesforce event to domain event with business logic"""
        if salesforce_event.event_type == "Created":
            return ClientCreatedEvent.create(
                aggregate_id=self.aggregate_id,
                data=salesforce_event.data,
                metadata=salesforce_event.metadata,
            )
        elif salesforce_event.event_type == "Updated":
            return ClientUpdatedEvent.create(
                aggregate_id=self.aggregate_id,
                data=salesforce_event.data,
                metadata=salesforce_event.metadata,
            )
        elif salesforce_event.event_type == "Deleted":
            return ClientDeletedEvent.create(
                aggregate_id=self.aggregate_id,
                data=salesforce_event.data,
                metadata=salesforce_event.metadata,
            )
        else:
            raise ValueError(
                f"Unknown event type: {salesforce_event.event_type}"
            )

    def _should_broadcast_event(self, event: DomainEvent) -> bool:
        """
        Business logic: Determine if event should be broadcasted.

        Rule: Don't broadcast events for inactive clients (they haven't signed yet)
        """
        # Extract status from event data
        status = None
        if event.event_type == "Created":
            status = event.data.get("status")
        elif event.event_type == "Updated":
            status = event.data.get("status")
        elif event.event_type == "Deleted":
            # Always broadcast deletions
            return True

        # Business rule: Don't broadcast inactive clients
        if status and status.lower() in ["inactive", "pending", "draft"]:
            logger.info(
                f"Client {self.aggregate_id} status '{status}' - event will not be broadcasted"
            )
            return False

        return True

    def apply(self, event: DomainEvent) -> None:
        """Apply a domain event to the client aggregate state"""
        # Track the event for business logic validation
        self.events.append(event)

        if event.event_type == "Created":
            self._apply_created_event(event)
        elif event.event_type == "Updated":
            self._apply_updated_event(event)
        elif event.event_type == "Deleted":
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    def create_from_salesforce(self, data: dict) -> None:
        """Create client from Salesforce data"""
        mapped_data = self.apply_mappings(data)

        # Apply only the fields needed for read model
        self.name = mapped_data.get("name")
        self.parent_id = mapped_data.get("parent_id")
        self.status = mapped_data.get("status")

        # Set creation timestamp
        created_date = mapped_data.get("created_date")
        if created_date:
            self.created_at = created_date
        else:
            self.created_at = datetime.utcnow()

        self.updated_at = self.created_at

    def update_from_salesforce(self, data: dict) -> None:
        """Update client from Salesforce data"""
        mapped_data = self.apply_mappings(data)

        # Update only provided fields
        if "name" in mapped_data:
            self.name = mapped_data["name"]
        if "parent_id" in mapped_data:
            self.parent_id = mapped_data["parent_id"]
        if "status" in mapped_data:
            self.status = mapped_data["status"]

        self.updated_at = datetime.utcnow()

    def delete_from_salesforce(self, data: dict) -> None:
        """Mark client as deleted from Salesforce data"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()

    def _apply_created_event(self, event: DomainEvent) -> None:
        """Apply client created event"""
        super()._apply_created_event(event)

        data = event.data
        self.name = data.get("name")
        self.parent_id = data.get("parent_id")
        self.status = data.get("status")

    def _apply_updated_event(self, event: DomainEvent) -> None:
        """Apply client updated event"""
        super()._apply_updated_event(event)

        data = event.data
        # Update only provided fields
        if "name" in data:
            self.name = data["name"]
        if "parent_id" in data:
            self.parent_id = data["parent_id"]
        if "status" in data:
            self.status = data["status"]

    def _apply_deleted_event(self, event: DomainEvent) -> None:
        """Apply client deleted event"""
        super()._apply_deleted_event(event)
