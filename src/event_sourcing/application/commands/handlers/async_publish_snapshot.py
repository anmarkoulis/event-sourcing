from typing import Dict, Any
import logging

from ..aggregate import AsyncPublishSnapshotCommand
from ...tasks.publish_snapshot import publish_snapshot_task

logger = logging.getLogger(__name__)


class AsyncPublishSnapshotCommandHandler:
    """Handler for asynchronously publishing snapshots via Celery"""
    
    def __init__(self):
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""
        pass
    
    async def handle(self, command: AsyncPublishSnapshotCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for publish snapshot command: {command.command_id}")
        
        # Extract data from command
        aggregate_id = command.data["aggregate_id"]
        aggregate_type = command.data["aggregate_type"]
        snapshot = command.data["snapshot"]
        event_type = command.data["event_type"]
        
        # Trigger Celery task
        task = publish_snapshot_task.delay(
            command_id=command.command_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot,
            event_type=event_type
        )
        
        logger.info(f"Celery task triggered with task_id: {task.id} for command: {command.command_id}") 