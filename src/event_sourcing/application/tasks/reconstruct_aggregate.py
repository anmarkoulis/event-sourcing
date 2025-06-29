import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync

from event_sourcing.application.commands.aggregate import (
    AsyncPublishSnapshotCommand,
    AsyncUpdateReadModelCommand,
    ReconstructAggregateCommand,
)
from event_sourcing.application.commands.handlers.async_publish_snapshot import (
    AsyncPublishSnapshotCommandHandler,
)
from event_sourcing.application.commands.handlers.async_update_read_model import (
    AsyncUpdateReadModelCommandHandler,
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
) -> Dict[str, Any]:
    """
    Reconstruct aggregate asynchronously.

    :param command_id: The ID of the command
    :param aggregate_id: The aggregate ID
    :param aggregate_type: The aggregate type
    :param entity_name: The Salesforce entity name
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    event_store = infrastructure_factory.event_store

    # Create handler
    handler = ReconstructAggregateCommandHandler(event_store)

    # Create command directly
    command = ReconstructAggregateCommand(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        entity_name=entity_name,
    )

    # Process command
    snapshot: Dict[str, Any] = await handler.handle(command)

    logger.info(
        f"Successfully reconstructed aggregate asynchronously: {command_id}"
    )
    return snapshot


async def trigger_next_steps(
    aggregate_id: str, aggregate_type: str, snapshot: Dict[str, Any]
) -> None:
    """Trigger the next steps in the processing chain"""
    logger.info(f"Triggering next steps for aggregate: {aggregate_id}")

    # Create and trigger update read model command
    update_command = AsyncUpdateReadModelCommand(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
    )

    update_handler = AsyncUpdateReadModelCommandHandler()
    await update_handler.handle(update_command)

    # Create and trigger publish snapshot command
    publish_command = AsyncPublishSnapshotCommand(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
        event_type="Updated",  # This should come from the original event
    )

    publish_handler = AsyncPublishSnapshotCommandHandler()
    await publish_handler.handle(publish_command)

    logger.info(f"Triggered next steps for aggregate: {aggregate_id}")


@app.task(
    name="reconstruct_aggregate",
)
@sync_error_logger
def reconstruct_aggregate_task(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    entity_name: str,
) -> Dict[str, Any]:
    """Reconstruct aggregate via Celery task."""
    logger.info(
        f"Starting Celery task for reconstruct aggregate command: {command_id}"
    )

    # Convert async function to sync for Celery
    reconstruct_aggregate_async_sync = async_to_sync(
        reconstruct_aggregate_async
    )
    trigger_next_steps_sync = async_to_sync(trigger_next_steps)

    # Set the event loop for the sync function
    reconstruct_aggregate_async_sync.main_event_loop = asyncio.get_event_loop()  # type: ignore
    trigger_next_steps_sync.main_event_loop = asyncio.get_event_loop()  # type: ignore

    # Execute the async function
    snapshot = reconstruct_aggregate_async_sync(
        command_id=command_id,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        entity_name=entity_name,
    )

    # Trigger the next steps in the chain
    trigger_next_steps_sync(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
    )

    logger.info(
        f"Completed Celery task for reconstruct aggregate command: {command_id}"
    )
    return snapshot
