import logging
from datetime import datetime

from event_sourcing.domain.aggregates.base import BaseAggregate
from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.domain.mappings.registry import MappingRegistry

logger = logging.getLogger(__name__)


class SalesforceAggregate(BaseAggregate):
    """Base aggregate for Salesforce entities"""

    def __init__(self, aggregate_id: str, entity_name: str):
        super().__init__(aggregate_id)
        self.entity_name = entity_name
        self.is_deleted = False
        self.created_at: datetime | None = None
        self.updated_at: datetime | None = None

    def apply_mappings(self, raw_data: dict) -> dict:
        """Apply field mappings to raw Salesforce data"""
        mappings_class = MappingRegistry.get_mappings(self.entity_name)
        if not mappings_class:
            logger.warning(f"No mappings found for entity: {self.entity_name}")
            return raw_data

        mappings = mappings_class.get_mappings()
        mapped_data = {}

        for key, mapping in mappings.items():
            try:
                mapped_data[key] = (
                    mapping.operation(raw_data, mapping.value)
                    if callable(mapping.operation)
                    else mapping.value
                )
            except KeyError:
                logger.debug(f"Field {key} not found in raw data")
                continue
            except Exception as e:
                logger.error(f"Error applying mapping for field {key}: {e}")
                continue

        return mapped_data

    def apply(self, event: DomainEvent) -> None:
        """Apply domain event to Salesforce aggregate state"""
        if event.event_type == "Created":
            self._apply_created_event(event)
        elif event.event_type == "Updated":
            self._apply_updated_event(event)
        elif event.event_type == "Deleted":
            self._apply_deleted_event(event)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")

    def _apply_created_event(self, event: DomainEvent) -> None:
        """Apply created event - to be implemented by subclasses"""
        self.created_at = event.timestamp
        self.updated_at = event.timestamp

    def _apply_updated_event(self, event: DomainEvent) -> None:
        """Apply updated event - to be implemented by subclasses"""
        self.updated_at = event.timestamp

    def _apply_deleted_event(self, event: DomainEvent) -> None:
        """Apply deleted event - to be implemented by subclasses"""
        self.is_deleted = True
        self.updated_at = event.timestamp
