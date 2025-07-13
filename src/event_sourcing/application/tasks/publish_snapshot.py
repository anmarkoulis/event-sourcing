import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.aggregate import (
    PublishSnapshotCommand,
)
from event_sourcing.config.celery_app import app
from event_sourcing.dto.event import EventDTO
from event_sourcing.infrastructure.provider import get_infrastructure_factory
from event_sourcing.utils import sync_error_logger

logger = logging.getLogger(__name__)


async def publish_snapshot_async(
    event: EventDTO,
) -> None:
    """
    Publish snapshot asynchronously.

    :param event: The EventDTO containing all snapshot info
    """
    # Extract fields from EventDTO
    aggregate_id = event.aggregate_id
    aggregate_type = event.aggregate_type
    snapshot = event.data.get("snapshot")
    event_type = event.event_type.value
    command_id = str(event.event_id)

    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    event_publisher = infrastructure_factory.event_publisher

    # Create handler using dynamic import
    from event_sourcing.application.commands.handlers.publish_snapshot import (
        PublishSnapshotCommandHandler,
    )

    handler = PublishSnapshotCommandHandler(event_publisher)

    # Create command directly
    command = PublishSnapshotCommand(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
        event_type=event_type,
    )

    # Process command
    await handler.handle(command)

    logger.info(
        f"Successfully published snapshot asynchronously: {command_id}"
    )


@app.task(
    name="publish_snapshot",
)
@sync_error_logger
def publish_snapshot_task(
    event_data: Dict[str, Any],
) -> None:
    """Publish snapshot via Celery task."""
    logger.info(f"Starting Celery task for publish snapshot")

    # Convert raw dict back to EventDTO for validation
    event = EventDTO(**event_data)
    logger.debug(f"EventDTO: {event}")

    # Convert async function to sync for Celery
    publish_snapshot_async_sync = async_to_sync(publish_snapshot_async)

    # Set the event loop for the sync function
    publish_snapshot_async_sync.main_event_loop = asyncio.get_event_loop()  # type: ignore

    # Execute the async function
    publish_snapshot_async_sync(event=event)

    logger.info(
        f"Completed Celery task for publish snapshot: {event.event_id}"
    )
