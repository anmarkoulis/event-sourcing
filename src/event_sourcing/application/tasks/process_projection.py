import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.projections.client_projection import (
    ClientProjection,
)
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.celery_app import app
from event_sourcing.utils import sync_error_logger

logger = logging.getLogger(__name__)


async def process_projection_async(
    task_name: str,
    event_data: Dict[str, Any],
    projection_type: str,
) -> None:
    """
    Process projection asynchronously.

    :param task_name: The name of the projection task to execute
    :param event_data: The event data to process
    :param projection_type: The type of projection (e.g., "client")
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    read_model = infrastructure_factory.read_model
    event_publisher = infrastructure_factory.event_publisher

    # Create projection instance
    if projection_type == "client":
        projection = ClientProjection(read_model, event_publisher)
    else:
        logger.error(f"Unknown projection type: {projection_type}")
        return

    # Route to appropriate projection handler
    if task_name == "process_client_created_projection":
        from event_sourcing.domain.events.base import DomainEvent

        event = DomainEvent(**event_data)
        await projection.handle_client_created(event)
    elif task_name == "process_client_updated_projection":
        from event_sourcing.domain.events.base import DomainEvent

        event = DomainEvent(**event_data)
        await projection.handle_client_updated(event)
    elif task_name == "process_client_deleted_projection":
        from event_sourcing.domain.events.base import DomainEvent

        event = DomainEvent(**event_data)
        await projection.handle_client_deleted(event)
    else:
        logger.error(f"Unknown task name: {task_name}")
        return

    logger.info(f"Successfully processed projection {task_name}")


@app.task(
    name="process_projection",
)
@sync_error_logger
def process_projection_task(
    task_name: str,
    event_data: Dict[str, Any],
    projection_type: str,
) -> None:
    """Process projection via Celery task."""
    logger.info(f"Starting Celery task for projection: {task_name}")

    # Convert async function to sync for Celery
    process_projection_async_sync = async_to_sync(process_projection_async)

    # Set the event loop for the sync function
    process_projection_async_sync.main_event_loop = asyncio.get_event_loop()  # type: ignore

    # Execute the async function
    process_projection_async_sync(
        task_name=task_name,
        event_data=event_data,
        projection_type=projection_type,
    )

    logger.info(f"Completed Celery task for projection: {task_name}")
