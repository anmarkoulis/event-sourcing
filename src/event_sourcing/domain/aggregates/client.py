import logging
from typing import List, Optional

from event_sourcing.domain.aggregates.salesforce import SalesforceAggregate
from event_sourcing.domain.events.base import DomainEvent

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

    def process_crm_event(self, crm_event: DomainEvent) -> List[DomainEvent]:
        """
        Process CRM event with pure business logic (provider-agnostic).

        Business Rules:
        1. Validate event sequence
        2. Only broadcast events for active clients (status != 'Inactive')
        """
        logger.info(
            f"Processing CRM event: {crm_event.event_type} for client {self.aggregate_id}"
        )

        # Business Rule 1: Validate event sequence
        if not self._is_valid_event_sequence(crm_event):
            raise ValueError(
                f"Invalid event sequence: {crm_event.event_type} for client {self.aggregate_id}"
            )

        # Business Rule 2: Check if event should be broadcasted
        if not self._should_broadcast_event(crm_event):
            logger.info(
                f"Event for client {self.aggregate_id} will not be broadcasted (inactive client)"
            )
            # Still return the event for storage, but mark it as non-broadcastable
            crm_event.metadata["broadcast"] = False
        else:
            crm_event.metadata["broadcast"] = True

        return [crm_event]

    def _is_valid_event_sequence(self, event: DomainEvent) -> bool:
        """Business logic: Validate event ordering"""
        if event.event_type == "Created" and self.events:
            logger.warning(
                f"CREATE event received for existing client {self.aggregate_id}"
            )
            return False

        if event.event_type != "Created" and not self.events:
            # This is handled by domain service or command handler
            return True

        return True

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
