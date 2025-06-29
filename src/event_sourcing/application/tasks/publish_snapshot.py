import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.aggregate import (
    PublishSnapshotCommand,
    PublishSnapshotCommandData,
)
from event_sourcing.application.commands.handlers.publish_snapshot import (
    PublishSnapshotCommandHandler,
)
from event_sourcing.application.services.infrastructure import (
    get_infrastructure_factory,
)
from event_sourcing.config.celery_app import app

logger = logging.getLogger(__name__)


async def publish_snapshot_async(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    snapshot: Dict[str, Any],
    event_type: str,
) -> None:
    """
    Publish snapshot asynchronously.

    :param command_id: The ID of the command
    :param aggregate_id: The aggregate ID
    :param aggregate_type: The aggregate type
    :param snapshot: The aggregate snapshot
    :param event_type: The event type (Created, Updated, Deleted)
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    event_publisher = infrastructure_factory.event_publisher

    # Create handler
    handler = PublishSnapshotCommandHandler(event_publisher)

    # Create command data
    data = PublishSnapshotCommandData(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
        event_type=event_type,
    )

    # Create command
    command = PublishSnapshotCommand.create(data=data.dict())

    # Process command
    await handler.handle(command)

    logger.info(
        f"Successfully published snapshot asynchronously: {command_id}"
    )


@app.task(
    name="publish_snapshot",
)
def publish_snapshot_task(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    snapshot: Dict[str, Any],
    event_type: str,
) -> None:
    """Publish snapshot via Celery task."""
    logger.info(
        f"Starting Celery task for publish snapshot command: {command_id}"
    )

    # Convert async function to sync for Celery
    publish_snapshot_async_sync = async_to_sync(publish_snapshot_async)

    # Set the event loop for the sync function
    publish_snapshot_async_sync.main_event_loop = asyncio.get_event_loop()

    # Execute the async function
    publish_snapshot_async_sync(
        command_id=command_id,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
        event_type=event_type,
    )

    logger.info(
        f"Completed Celery task for publish snapshot command: {command_id}"
    )
