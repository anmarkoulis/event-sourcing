import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.crm import ProcessCRMEventCommand
from event_sourcing.config.celery_app import app
from event_sourcing.infrastructure.provider import get_infrastructure_factory
from event_sourcing.utils import sync_error_logger

logger = logging.getLogger(__name__)


async def process_crm_event_async(
    command_id: str,
    raw_event: Dict[str, Any],
    provider: str,
    entity_type: str,
) -> None:
    """
    Process CRM event asynchronously.

    :param command_id: The ID of the command
    :param raw_event: Raw CRM event
    :param provider: CRM provider name (salesforce, hubspot, etc.)
    :param entity_type: Entity type (client, deal, etc.)
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()

    # Create handler using factory method
    handler = infrastructure_factory.create_process_crm_event_command_handler()

    # Create command directly
    command = ProcessCRMEventCommand(
        raw_event=raw_event,
        provider=provider,
        entity_type=entity_type,
    )

    # Process command
    await handler.handle(command)

    logger.info(
        f"Successfully processed {provider} CRM event asynchronously: {command_id}"
    )


@app.task(
    name="process_crm_event",
)
@sync_error_logger
def process_crm_event_task(
    command_id: str,
    raw_event: Dict[str, Any],
    provider: str,
    entity_type: str,
) -> None:
    """Process CRM event via Celery task."""
    logger.info(
        f"Starting Celery task for process CRM event command: {command_id}"
    )

    # Convert async function to sync for Celery
    process_crm_event_async_sync = async_to_sync(process_crm_event_async)

    # Set the event loop for the sync function
    process_crm_event_async_sync.main_event_loop = (  # type: ignore[attr-defined]
        asyncio.get_event_loop()
    )

    # Execute the async function
    process_crm_event_async_sync(
        command_id=command_id,
        raw_event=raw_event,
        provider=provider,
        entity_type=entity_type,
    )

    logger.info(
        f"Completed Celery task for process CRM event command: {command_id}"
    )
