import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends

from event_sourcing.api.depends import DependencyService
from event_sourcing.application.commands.handlers.async_process_salesforce_event import (
    AsyncProcessSalesforceEventCommandHandler,
)
from event_sourcing.application.commands.salesforce import (
    AsyncProcessSalesforceEventCommand,
)

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post("/salesforce/", description="Process Salesforce CDC event")
async def process_salesforce_event(
    raw_event: Dict[str, Any],
    handler: AsyncProcessSalesforceEventCommandHandler = Depends(
        DependencyService.get_async_process_salesforce_event_command_handler
    ),
) -> Dict[str, Any]:
    """
    Process a Salesforce CDC event asynchronously via Celery.

    This endpoint will:
    1. Create an async command
    2. Trigger a Celery task
    3. Return immediately with task information
    """
    logger.info(f"Processing Salesforce event asynchronously: {raw_event}")

    # Extract event metadata
    change_event_header = (
        raw_event.get("detail", {})
        .get("payload", {})
        .get("ChangeEventHeader", {})
    )
    entity_name = change_event_header.get("entityName")
    change_type = change_event_header.get("changeType")

    # Create async command
    command = AsyncProcessSalesforceEventCommand.create(
        raw_event=raw_event, entity_name=entity_name, change_type=change_type
    )

    # Process command (triggers Celery task)
    await handler.handle(command)

    logger.info(
        f"Successfully triggered async processing for Salesforce event: {command.command_id}"
    )

    return {
        "status": "success",
        "command_id": command.command_id,
        "message": "Event processing started asynchronously",
        "entity_name": entity_name,
        "change_type": change_type,
        "processing": "async",
    }
