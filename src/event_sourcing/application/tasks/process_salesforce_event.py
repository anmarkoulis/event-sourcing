import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.handlers.process_salesforce_event import (
    ProcessSalesforceEventCommandHandler,
)
from event_sourcing.application.commands.salesforce import (
    ProcessSalesforceEventCommand,
)
from event_sourcing.application.services.backfill import BackfillService
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.celery_app import app

logger = logging.getLogger(__name__)


async def process_salesforce_event_async(
    command_id: str,
    raw_event: Dict[str, Any],
    entity_name: str,
    change_type: str,
) -> None:
    """
    Process Salesforce event asynchronously.

    :param command_id: The ID of the command
    :param raw_event: Raw Salesforce CDC event
    :param entity_name: Salesforce entity name
    :param change_type: Type of change (CREATE, UPDATE, DELETE)
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    event_store = infrastructure_factory.event_store
    read_model = infrastructure_factory.read_model
    event_publisher = infrastructure_factory.event_publisher

    # Create backfill service
    backfill_service = BackfillService(None, event_store)

    # Create handler
    handler = ProcessSalesforceEventCommandHandler(
        event_store=event_store,
        read_model=read_model,
        event_publisher=event_publisher,
        backfill_service=backfill_service,
    )

    # Create command
    command = ProcessSalesforceEventCommand.create(
        raw_event=raw_event, entity_name=entity_name, change_type=change_type
    )

    # Process command
    await handler.handle(command)

    logger.info(
        f"Successfully processed Salesforce event asynchronously: {command_id}"
    )


@app.task(
    name="process_salesforce_event",
)
def process_salesforce_event_task(
    command_id: str,
    raw_event: Dict[str, Any],
    entity_name: str,
    change_type: str,
) -> None:
    """Process Salesforce event via Celery task."""
    logger.info(f"Starting Celery task for command: {command_id}")

    # Convert async function to sync for Celery
    process_salesforce_event_async_sync = async_to_sync(
        process_salesforce_event_async
    )

    # Set the event loop for the sync function
    process_salesforce_event_async_sync.main_event_loop = (
        asyncio.get_event_loop()
    )

    # Execute the async function
    process_salesforce_event_async_sync(
        command_id=command_id,
        raw_event=raw_event,
        entity_name=entity_name,
        change_type=change_type,
    )

    logger.info(f"Completed Celery task for command: {command_id}")
