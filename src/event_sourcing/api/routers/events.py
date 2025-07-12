import logging
from typing import Any, Dict

from fastapi import APIRouter

from event_sourcing.api.depends import InfrastructureFactoryDep
from event_sourcing.application.commands.crm import AsyncProcessCRMEventCommand

logger = logging.getLogger(__name__)

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post(
    "/crm/{provider}/",
    description="Process CRM event from any provider asynchronously via Celery",
)
async def process_crm_event(
    provider: str,  # "salesforce", "hubspot", etc.
    raw_event: Dict[str, Any],
    infrastructure_factory: InfrastructureFactoryDep,
) -> Dict[str, Any]:
    """
    Process CRM event from any provider asynchronously via Celery.

    This endpoint will:
    1. Create an async command
    2. Trigger a Celery task
    3. Return immediately with task information
    """
    logger.info(f"Processing {provider} event asynchronously: {raw_event}")

    # Extract entity type from the event (this could be made more sophisticated)
    entity_type = "client"  # Default to client for now

    # Create async command directly
    command = AsyncProcessCRMEventCommand(
        raw_event=raw_event,
        provider=provider,
        entity_type=entity_type,
    )

    # Create handler using factory method
    handler = (
        infrastructure_factory.create_async_process_crm_event_command_handler()
    )

    # Process command (triggers Celery task)
    await handler.handle(command)

    logger.info(
        f"Successfully triggered async processing for {provider} event"
    )

    return {
        "status": "success",
        "command_id": "",  # We'll need to handle this differently
        "message": "Event processing started asynchronously",
        "provider": provider,
        "entity_type": entity_type,
        "processing": "async",
    }
