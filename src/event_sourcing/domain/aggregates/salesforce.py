import logging
from abc import abstractmethod
from typing import Any, Dict

from event_sourcing.domain.aggregates.base import BaseAggregate
from event_sourcing.domain.events.base import DomainEvent
from event_sourcing.domain.mappings.registry import MappingRegistry

logger = logging.getLogger(__name__)


class SalesforceAggregate(BaseAggregate):
    """Base aggregate for Salesforce entities with common Salesforce operations"""

    def __init__(self, aggregate_id: str, entity_name: str):
        super().__init__(aggregate_id)
        self.entity_name = entity_name
        self.is_deleted = False

    @abstractmethod
    def create_from_salesforce(self, data: dict) -> None:
        """Create aggregate from Salesforce data"""

    @abstractmethod
    def update_from_salesforce(self, data: dict) -> None:
        """Update aggregate from Salesforce data"""

    @abstractmethod
    def delete_from_salesforce(self, data: dict) -> None:
        """Mark aggregate as deleted from Salesforce data"""

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

    def validate_event_ordering(self, event: DomainEvent) -> bool:
        """Validate event ordering and consistency for Salesforce entities"""
        if event.event_type == "Created":
            # Creation event should be first
            if self.version > 0:
                logger.warning(
                    f"Creation event received for existing {self.entity_name} {self.aggregate_id}"
                )
                return False
            return True
        else:
            # Non-creation events require existing entity
            if self.version == 0:
                logger.warning(
                    f"Non-creation event received for non-existent {self.entity_name} {self.aggregate_id}"
                )
                return False
            return True

    def handle_backfill_scenario(self, event: DomainEvent) -> None:
        """Handle backfill scenarios by triggering backfill"""
        if not self.validate_event_ordering(event):
            logger.info(
                f"Triggering backfill for {self.entity_name} {self.aggregate_id}"
            )
            # This will be handled by the command handler
            # We just log the scenario here
            logger.info(
                f"Backfill needed for {self.entity_name} {self.aggregate_id}"
            )

    def get_snapshot(self) -> Dict[str, Any]:
        """Return current state snapshot with common Salesforce fields"""
        snapshot = {
            "aggregate_id": self.aggregate_id,
            "entity_name": self.entity_name,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_deleted": self.is_deleted,
        }
        return snapshot
