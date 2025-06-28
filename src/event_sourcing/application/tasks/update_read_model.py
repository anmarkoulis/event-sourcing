import asyncio
from typing import Dict, Any
import logging

from asgiref.sync import async_to_sync

from ...config.celery_app import app
from ..commands.aggregate import UpdateReadModelCommand
from ..commands.handlers.update_read_model import UpdateReadModelCommandHandler
from ..services.infrastructure import get_infrastructure_factory

logger = logging.getLogger(__name__)


async def update_read_model_async(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    snapshot: Dict[str, Any],
) -> None:
    """
    Update read model asynchronously.
    
    :param command_id: The ID of the command
    :param aggregate_id: The aggregate ID
    :param aggregate_type: The aggregate type
    :param snapshot: The aggregate snapshot
    """
    # Get infrastructure components
    infrastructure_factory = get_infrastructure_factory()
    read_model = infrastructure_factory.read_model
    
    # Create handler
    handler = UpdateReadModelCommandHandler(read_model)
    
    # Create command
    command = UpdateReadModelCommand.create(
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot
    )
    
    # Process command
    await handler.handle(command)
    
    logger.info(f"Successfully updated read model asynchronously: {command_id}")


@app.task(
    name="update_read_model",
)
def update_read_model_task(
    command_id: str,
    aggregate_id: str,
    aggregate_type: str,
    snapshot: Dict[str, Any],
) -> None:
    """Update read model via Celery task."""
    logger.info(f"Starting Celery task for update read model command: {command_id}")
    
    # Convert async function to sync for Celery
    update_read_model_async_sync = async_to_sync(update_read_model_async)
    
    # Set the event loop for the sync function
    update_read_model_async_sync.main_event_loop = asyncio.get_event_loop()
    
    # Execute the async function
    update_read_model_async_sync(
        command_id=command_id,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        snapshot=snapshot,
    )
    
    logger.info(f"Completed Celery task for update read model command: {command_id}") 