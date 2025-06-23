from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from ..depends import DependencyService
from ...application.commands.salesforce import ProcessSalesforceEventCommand
from ...application.commands.handlers.process_salesforce_event import ProcessSalesforceEventCommandHandler

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post("/salesforce/", description="Process Salesforce CDC event")
async def process_salesforce_event(
    raw_event: Dict[str, Any],
    handler: ProcessSalesforceEventCommandHandler = Depends(DependencyService.get_process_salesforce_event_command_handler)
) -> Dict[str, Any]:
    """
    Process a Salesforce CDC event and see the full event sourcing flow.
    
    This endpoint will:
    1. Validate the event
    2. Create domain events
    3. Save to event store
    4. Update read model
    5. Publish normalized events
    """
    logger.info(f"Processing Salesforce event: {raw_event}")
    
    # Extract event metadata
    change_event_header = raw_event.get("detail", {}).get("payload", {}).get("ChangeEventHeader", {})
    entity_name = change_event_header.get("entityName")
    change_type = change_event_header.get("changeType")
    
    # Create command
    command = ProcessSalesforceEventCommand.create(
        raw_event=raw_event,
        entity_name=entity_name,
        change_type=change_type
    )
    
    # Process command
    await handler.handle(command)
    
    logger.info(f"Successfully processed Salesforce event: {command.command_id}")
    
    return {
        "status": "success",
        "command_id": command.command_id,
        "message": "Event processed successfully",
        "entity_name": entity_name,
        "change_type": change_type
    } 