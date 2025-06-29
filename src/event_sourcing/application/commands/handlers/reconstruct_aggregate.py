import logging
from typing import Any, Dict

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

    async def handle(
        self, command: ReconstructAggregateCommand
    ) -> Dict[str, Any]:
        """Handle reconstruct aggregate command"""
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
            return {}

        logger.info(f"Events found for aggregate: {events}")

        # Get aggregate class from registry
        aggregate_class = AggregateRegistry.get_aggregate(aggregate_type)
        if not aggregate_class:
            logger.error(
                f"No aggregate class found for type: {aggregate_type}"
            )
            return {}

        # Create aggregate instance and apply events
        aggregate = aggregate_class(aggregate_id)
        logger.info(f"Aggregate created: {aggregate}")

        # Apply events with mappings
        for event in events:
            # Apply mappings during reconstruction
            mapped_data = self._apply_mappings(event.data, entity_name)
            event.data = mapped_data
            aggregate.apply(event)

        # Build read model from events (not from aggregate state)
        read_model = self._build_read_model_from_events(events, entity_name)

        logger.info(
            f"Generated read model for {aggregate_type} {aggregate_id}: {read_model}"
        )

        logger.info(
            f"Successfully reconstructed aggregate: {aggregate_type} {aggregate_id}"
        )
        return read_model

    def _build_read_model_from_events(
        self, events: list, entity_name: str
    ) -> Dict[str, Any]:
        """Build read model from events instead of aggregate state"""
        read_model = {
            "aggregate_id": events[0].aggregate_id if events else None,
            "entity_name": entity_name,
        }

        # Apply each event to build the current state
        for event in events:
            mapped_data = self._apply_mappings(event.data, entity_name)

            if event.event_type == "Created":
                read_model.update(mapped_data)
                read_model["created_at"] = event.timestamp
                read_model["updated_at"] = event.timestamp
            elif event.event_type == "Updated":
                # Only update fields that are present in the event
                for key, value in mapped_data.items():
                    if value is not None:
                        read_model[key] = value
                read_model["updated_at"] = event.timestamp
            elif event.event_type == "Deleted":
                read_model["is_deleted"] = True
                read_model["updated_at"] = event.timestamp

        return read_model

    def _apply_mappings(
        self, event_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
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
