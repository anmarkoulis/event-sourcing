import logging
import uuid
from typing import List, Optional

from event_sourcing.domain.aggregates.salesforce import SalesforceAggregate
from event_sourcing.dto.event import EventDTO

logger = logging.getLogger(__name__)


class ClientAggregate(SalesforceAggregate):
    """Client domain aggregate - encapsulates client business logic"""

    def __init__(self, aggregate_id: uuid.UUID):
        super().__init__(aggregate_id, "Account")

        # Track events for business logic validation
        self.events: List[EventDTO] = []

        # Client-specific attributes (only what's needed for read model)
        self.name: Optional[str] = None
        self.parent_id: Optional[str] = None
        self.status: Optional[str] = None

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
        super()._apply_created_event(event)

        data = event.data
        self.name = data.get("name")
        self.parent_id = data.get("parent_id")
        self.status = data.get("status")

    def _apply_updated_event(self, event: EventDTO) -> None:
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

    def _apply_deleted_event(self, event: EventDTO) -> None:
        """Apply client deleted event"""
        super()._apply_deleted_event(event)
        # Mark as deleted (could set a deleted flag or clear fields)
        self.name = None
        self.parent_id = None
        self.status = None
