import logging

from event_sourcing.domain.aggregates.base import Aggregate
from event_sourcing.dto.event import EventDTO

logger = logging.getLogger(__name__)


class SalesforceAggregate(Aggregate):
    """Base Salesforce aggregate with common Salesforce-specific logic"""

    def __init__(self, aggregate_id: str, entity_type: str):
        super().__init__(aggregate_id)
        self.entity_type = entity_type
        self.events: list[EventDTO] = []

    def apply(self, event: EventDTO) -> None:
        """Apply a domain event to the aggregate state"""
        # Track the event for business logic validation
        self.events.append(event)

        # Apply based on event type
        if event.event_type.value == "CLIENT_CREATED":
            self._apply_created_event(event)
        elif event.event_type.value == "CLIENT_UPDATED":
            self._apply_updated_event(event)
        elif event.event_type.value == "CLIENT_DELETED":
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    def _apply_created_event(self, event: EventDTO) -> None:
        """Apply created event - override in subclasses"""
        logger.info(f"Applied created event: {event.event_id}")

    def _apply_updated_event(self, event: EventDTO) -> None:
        """Apply updated event - override in subclasses"""
        logger.info(f"Applied updated event: {event.event_id}")

    def _apply_deleted_event(self, event: EventDTO) -> None:
        """Apply deleted event - override in subclasses"""
        logger.info(f"Applied deleted event: {event.event_id}")
