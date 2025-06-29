import asyncio
import logging

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.aggregate import (
    ReconstructAggregateCommand,
)
from event_sourcing.application.commands.handlers.reconstruct_aggregate import (
    ReconstructAggregateCommandHandler,
)
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.celery_app import app
from event_sourcing.utils import sync_error_logger

logger = logging.getLogger(__name__)


async def reconstruct_aggregate_async(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    entity_name: str,
) -> None:
    """
    Reconstruct aggregate asynchronously for business logic validation.

    :param command_id: The ID of the command
    :param aggregate_id: The aggregate ID
    :param aggregate_type: The aggregate type
    :param entity_name: The Salesforce entity name
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    event_store = infrastructure_factory.event_store

    # Create reconstruction handler
    reconstruct_handler = ReconstructAggregateCommandHandler(event_store)

    # Create command
    command = ReconstructAggregateCommand(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        entity_name=entity_name,
    )

    # Reconstruct aggregate (for business logic validation)
    aggregate = await reconstruct_handler.handle(command)

    if not aggregate:
        logger.warning(f"No aggregate reconstructed for {aggregate_id}")
        return

    logger.info(
        f"Successfully reconstructed aggregate for business logic validation: {command_id}"
    )


@app.task(
    name="reconstruct_aggregate",
)
@sync_error_logger
def reconstruct_aggregate_task(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    entity_name: str,
) -> None:
    """Reconstruct aggregate for business logic validation via Celery task."""
    logger.info(
        f"Starting Celery task for reconstruct aggregate command: {command_id}"
    )

    # Convert async function to sync for Celery
    reconstruct_aggregate_async_sync = async_to_sync(
        reconstruct_aggregate_async
    )

    # Set the event loop for the sync function
    reconstruct_aggregate_async_sync.main_event_loop = asyncio.get_event_loop()  # type: ignore

    # Execute the async function
    reconstruct_aggregate_async_sync(
        command_id=command_id,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        entity_name=entity_name,
    )

    logger.info(
        f"Completed Celery task for reconstruct aggregate command: {command_id}"
    )
