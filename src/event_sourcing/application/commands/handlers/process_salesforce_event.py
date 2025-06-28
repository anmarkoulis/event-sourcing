import logging
from typing import List
from datetime import datetime
import uuid

from ....domain.events.base import DomainEvent
from ....domain.events.client import ClientCreatedEvent, ClientUpdatedEvent, ClientDeletedEvent
from ....domain.mappings.registry import MappingRegistry
from ..salesforce import ProcessSalesforceEventCommand
from ..aggregate import AsyncReconstructAggregateCommand, AsyncUpdateReadModelCommand, AsyncPublishSnapshotCommand
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
            
            # 4. Create async commands for the next steps
            await self._create_async_follow_up_commands(parsed_event, command.data['entity_name'])
    
    async def _create_async_follow_up_commands(self, event: DomainEvent, entity_name: str) -> None:
        """Create async follow-up commands that will trigger Celery tasks"""
        
        # Only trigger the reconstruct aggregate command first
        # The subsequent steps will be triggered by the completion of this step
        reconstruct_command = AsyncReconstructAggregateCommand.create(
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            entity_name=entity_name
        )
        
        # Process only the reconstruct command (this will trigger the chain)
        await self._process_reconstruct_command(reconstruct_command)
    
    async def _process_reconstruct_command(self, reconstruct_command: AsyncReconstructAggregateCommand) -> None:
        """Process the reconstruct command by triggering Celery task"""
        
        # Trigger reconstruct aggregate task
        from .async_reconstruct_aggregate import AsyncReconstructAggregateCommandHandler
        reconstruct_handler = AsyncReconstructAggregateCommandHandler()
        await reconstruct_handler.handle(reconstruct_command)
        
        logger.info(f"Triggered reconstruct aggregate command for: {reconstruct_command.data['aggregate_id']}")
    
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