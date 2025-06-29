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
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.celery_app import app
from event_sourcing.utils import sync_error_logger

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

    # Create handler
    handler = ProcessSalesforceEventCommandHandler(
        event_store=event_store,
        read_model=read_model,
        event_publisher=event_publisher,
    )

    # Create command directly
    command = ProcessSalesforceEventCommand(
        raw_event=raw_event,
        entity_name=entity_name,
        change_type=change_type,
    )

    # Process command
    await handler.handle(command)

    logger.info(
        f"Successfully processed Salesforce event asynchronously: {command_id}"
    )


@app.task(
    name="process_salesforce_event",
)
@sync_error_logger
def process_salesforce_event_task(
    command_id: str,
    raw_event: Dict[str, Any],
    entity_name: str,
    change_type: str,
) -> None:
    """Process Salesforce event via Celery task."""
    logger.info(
        f"Starting Celery task for process Salesforce event command: {command_id}"
    )

    # Convert async function to sync for Celery
    process_salesforce_event_async_sync = async_to_sync(
        process_salesforce_event_async
    )

    # Set the event loop for the sync function
    process_salesforce_event_async_sync.main_event_loop = (  # type: ignore[attr-defined]
        asyncio.get_event_loop()
    )

    # Execute the async function
    process_salesforce_event_async_sync(
        command_id=command_id,
        raw_event=raw_event,
        entity_name=entity_name,
        change_type=change_type,
    )

    logger.info(
        f"Completed Celery task for process Salesforce event command: {command_id}"
    )
