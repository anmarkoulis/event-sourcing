import logging
from typing import Dict, Any

from ....domain.aggregates.registry import AggregateRegistry
from ....domain.mappings.registry import MappingRegistry
from ....infrastructure.event_store import EventStore
from ..aggregate import ReconstructAggregateCommand

logger = logging.getLogger(__name__)


class ReconstructAggregateCommandHandler:
    """Handler for reconstructing aggregates from events"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def handle(self, command: ReconstructAggregateCommand) -> Dict[str, Any]:
        """Handle reconstruct aggregate command"""
        aggregate_id = command.data["aggregate_id"]
        aggregate_type = command.data["aggregate_type"]
        entity_name = command.data["entity_name"]
        
        logger.info(f"Reconstructing aggregate: {aggregate_type} {aggregate_id}")
        
        # Get events for the aggregate
        events = await self.event_store.get_events(aggregate_id, aggregate_type)
        
        if not events:
            logger.warning(f"No events found for aggregate: {aggregate_type} {aggregate_id}")
            return {}
        
        # Get aggregate class from registry
        aggregate_class = AggregateRegistry.get_aggregate(aggregate_type)
        if not aggregate_class:
            logger.error(f"No aggregate class found for type: {aggregate_type}")
            return {}
        
        # Create aggregate instance
        aggregate = aggregate_class(aggregate_id)
        
        # Apply events with mappings
        for event in events:
            # Apply mappings during reconstruction
            mapped_data = self._apply_mappings(event.data, entity_name)
            event.data = mapped_data
            aggregate.apply(event)
        
        # Get snapshot
        snapshot = aggregate.get_snapshot()
        
        logger.info(f"Generated snapshot for {aggregate_type} {aggregate_id}: {snapshot}")
        
        logger.info(f"Successfully reconstructed aggregate: {aggregate_type} {aggregate_id}")
        return snapshot
    
    def _apply_mappings(self, raw_data: dict, entity_name: str) -> dict:
        """Apply field mappings to raw data"""
        mappings_class = MappingRegistry.get_mappings(entity_name)
        if not mappings_class:
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
                continue
        
        return mapped_data 