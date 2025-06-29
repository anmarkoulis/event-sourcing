import logging
from datetime import datetime
from typing import Optional

from event_sourcing.domain.aggregates.salesforce import SalesforceAggregate
from event_sourcing.domain.events.base import DomainEvent

logger = logging.getLogger(__name__)


class ClientAggregate(SalesforceAggregate):
    """Client domain aggregate - encapsulates client business logic"""

    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id, "Account")

        # Client-specific attributes (only what's needed for read model)
        self.name: Optional[str] = None
        self.parent_id: Optional[str] = None
        self.status: Optional[str] = None

    def apply(self, event: DomainEvent) -> None:
        """Apply a domain event to the client aggregate state"""
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
