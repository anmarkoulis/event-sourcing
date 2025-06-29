import logging
from typing import Any

from event_sourcing.application.commands.aggregate import (
    ReconstructAggregateCommand,
)
from event_sourcing.domain.aggregates.registry import AggregateRegistry
from event_sourcing.domain.mappings.registry import MappingRegistry
from event_sourcing.infrastructure.event_store import EventStore

logger = logging.getLogger(__name__)


class ReconstructAggregateCommandHandler:
    """Handler for reconstructing aggregates from events"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def handle(self, command: ReconstructAggregateCommand) -> Any:
        """Handle reconstruct aggregate command - returns the aggregate instance"""
        aggregate_id = command.aggregate_id
        aggregate_type = command.aggregate_type
        entity_name = command.entity_name

        logger.info(
            f"Reconstructing aggregate: {aggregate_type} {aggregate_id}"
        )

        # Get events for the aggregate
        events = await self.event_store.get_events(
            aggregate_id, aggregate_type
        )

        if not events:
            logger.warning(
                f"No events found for aggregate: {aggregate_type} {aggregate_id}"
            )
            return None

        logger.info(f"Events found for aggregate: {events}")

        # Get aggregate class from registry
        aggregate_class = AggregateRegistry.get_aggregate(aggregate_type)
        if not aggregate_class:
            logger.error(
                f"No aggregate class found for type: {aggregate_type}"
            )
            return None

        # Create aggregate instance and apply events
        aggregate = aggregate_class(aggregate_id)
        logger.info(f"Aggregate created: {aggregate}")

        # Apply events with mappings
        for event in events:
            # Apply mappings during reconstruction
            mapped_data = self._apply_mappings(event.data, entity_name)
            event.data = mapped_data
            aggregate.apply(event)

        logger.info(
            f"Successfully reconstructed aggregate: {aggregate_type} {aggregate_id}"
        )
        return aggregate

    def _apply_mappings(self, event_data: dict, entity_name: str) -> dict:
        """Apply field mappings to event data"""
        mappings_class = MappingRegistry.get_mappings(entity_name)
        if not mappings_class:
            logger.warning(f"No mappings found for entity: {entity_name}")
            return event_data

        mappings = mappings_class.get_mappings()
        mapped_data = {}

        for key, mapping in mappings.items():
            try:
                mapped_data[key] = (
                    mapping.operation(event_data, mapping.value)
                    if callable(mapping.operation)
                    else mapping.value
                )
            except KeyError:
                logger.debug(f"Field {key} not found in event data")
                continue
            except Exception as e:
                logger.error(f"Error applying mapping for field {key}: {e}")
                continue

        return mapped_data
