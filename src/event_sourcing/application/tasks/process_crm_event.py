import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.crm import ProcessCRMEventCommand
from event_sourcing.config.celery_app import app
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.provider import get_infrastructure_factory
from event_sourcing.utils import sync_error_logger

logger = logging.getLogger(__name__)


async def process_crm_event_async(
    event_data: Dict[str, Any],
) -> None:
    """
    Process CRM event asynchronously.

    :param event_data: The event data to process
    """
    event = EventDTO(**event_data)
    logger.info(
        f"Processing {event.source.value} event asynchronously: {event}"
    )
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()

    # Create handler using factory method
    handler = infrastructure_factory.create_process_crm_event_command_handler()
    logger.debug(f"Handler: {handler}")

    # Create command with EventDTO
    command = ProcessCRMEventCommand(
        event=event,
        provider=event.source.value,
    )
    logger.debug(f"Command: {command}")

    # Process command
    await handler.handle(command)
    logger.debug(f"Command handled")

    logger.info(
        f"Successfully processed {event.source.value} CRM event asynchronously: {event.event_id}"
    )


@app.task(
    name="process_crm_event",
)
@sync_error_logger
def process_crm_event_task(
    event_data: Dict[str, Any],
) -> None:
    """Process CRM event via Celery task."""
    logger.info(f"Starting Celery task for process CRM event")

    # Convert async function to sync for Celery
    process_crm_event_async_sync = async_to_sync(process_crm_event_async)

    # Set the event loop for the sync function
    process_crm_event_async_sync.main_event_loop = (  # type: ignore[attr-defined]
        asyncio.get_event_loop()
    )

    # Execute the async function
    process_crm_event_async_sync(event_data=event_data)

    logger.info(f"Completed Celery task for process CRM event: {event_data}")
