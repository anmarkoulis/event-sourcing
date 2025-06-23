import logging
from typing import List
from datetime import datetime
import uuid

from ....domain.events.base import DomainEvent
from ....domain.events.client import ClientCreatedEvent, ClientUpdatedEvent, ClientDeletedEvent
from ....domain.aggregates.client import ClientAggregate
from ....domain.mappings.registry import MappingRegistry
from ..salesforce import ProcessSalesforceEventCommand
from ....infrastructure.event_store import EventStore
from ....infrastructure.read_model import ReadModel
from ....infrastructure.messaging import EventPublisher
from ...services.backfill import BackfillService

logger = logging.getLogger(__name__)


class ProcessSalesforceEventCommandHandler:
    """Handler for processing Salesforce CDC events"""
    
    def __init__(self, event_store: EventStore, read_model: ReadModel, 
                 event_publisher: EventPublisher, backfill_service: BackfillService):
        self.event_store = event_store
        self.read_model = read_model
        self.event_publisher = event_publisher
        self.backfill_service = backfill_service
    
    async def handle(self, command: ProcessSalesforceEventCommand) -> None:
        """Handle process Salesforce event command"""
        logger.info(f"Processing Salesforce event: {command.data['raw_event']}")
        
        # 1. Parse and validate raw event
        parsed_events = self._parse_salesforce_event(command.data['raw_event'])
        logger.info(f"Parsed events: {parsed_events}")
        
        for parsed_event in parsed_events:
            logger.info(f"Processing parsed event: {parsed_event}")
            # 2. Validate event ordering and consistency
            is_valid = await self._validate_event_ordering(parsed_event)
            if not is_valid:
                logger.warning(f"Event validation failed: {parsed_event}")
                continue
            
            # 3. Store raw event
            await self.event_store.save_event(parsed_event)
            logger.info(f"Saved event: {parsed_event}")
            
            # 4. Reconstruct aggregate with mappings
            client = await self._reconstruct_aggregate(parsed_event.aggregate_id)
            logger.info(f"Reconstructed aggregate: {client}")
            # 5. Update read model
            await self.read_model.save_client(client.get_snapshot())
            logger.info(f"Updated read model: {client.get_snapshot()}")
            # 6. Publish normalized entity
            await self.event_publisher.publish(client.get_snapshot())
    
    def _parse_salesforce_event(self, raw_event: dict) -> List[DomainEvent]:
        """Parse Salesforce CDC event into domain events"""
        try:
            # Extract the payload from the CDC event structure
            payload = raw_event.get("detail", {}).get("payload", {})
            change_event_header = payload.get("ChangeEventHeader", {})
            
            entity_name = change_event_header.get("entityName")
            change_type = change_event_header.get("changeType")
            record_ids = change_event_header.get("recordIds", [])
            
            if not record_ids:
                logger.warning("No record IDs found in ChangeEventHeader")
                return []
            
            record_id = record_ids[0]  # Take the first record ID
            
            # Create metadata for the event
            metadata = {
                "source": "salesforce",
                "entity_name": entity_name,
                "change_type": change_type,
                "record_id": record_id,
                "commit_timestamp": change_event_header.get("commitTimestamp")
            }
            
            events = []
            
            # Map Salesforce entity names to our domain entities
            if entity_name == "Account":
                # Create appropriate domain event based on change type
                if change_type == "CREATE":
                    event = ClientCreatedEvent.create(
                        client_id=record_id,
                        data=payload,
                        metadata=metadata
                    )
                    events.append(event)
                elif change_type == "UPDATE":
                    event = ClientUpdatedEvent.create(
                        client_id=record_id,
                        data=payload,
                        metadata=metadata
                    )
                    events.append(event)
                elif change_type == "DELETE":
                    event = ClientDeletedEvent.create(
                        client_id=record_id,
                        data=payload,
                        metadata=metadata
                    )
                    events.append(event)
                else:
                    logger.warning(f"Unsupported change type: {change_type}")
            else:
                logger.warning(f"Unsupported entity type: {entity_name}")
            
            logger.info(f"Created {len(events)} domain events from Salesforce event")
            return events
            
        except Exception as e:
            logger.error(f"Error parsing Salesforce event: {e}")
            return []
    
    async def _validate_event_ordering(self, event: DomainEvent) -> bool:
        """Validate event ordering and consistency"""
        existing_events = await self.event_store.get_events(event.aggregate_id, event.aggregate_type)
        
        if event.event_type == "Created":
            if existing_events:
                logger.warning(f"Creation event received for existing aggregate {event.aggregate_id}")
                return False
        else:
            if not existing_events:
                logger.warning(f"Non-creation event received for non-existent aggregate {event.aggregate_id}")
                # Trigger backfill
                await self.backfill_service.trigger_backfill(event.aggregate_id, event.aggregate_type)
                return False
        
        return True
    
    async def _reconstruct_aggregate(self, aggregate_id: str) -> ClientAggregate:
        """Reconstruct aggregate from events with mappings applied"""
        events = await self.event_store.get_events(aggregate_id, "client")
        client = ClientAggregate(aggregate_id)
        
        for event in events:
            # Apply mappings during reconstruction
            mapped_data = self._apply_mappings(event.data, "Account")
            event.data = mapped_data
            client.apply(event)
        
        return client
    
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