from typing import Dict, Any
import logging

from ..aggregate import AsyncUpdateReadModelCommand
from ...tasks.update_read_model import update_read_model_task

logger = logging.getLogger(__name__)


class AsyncUpdateReadModelCommandHandler:
    """Handler for asynchronously updating read models via Celery"""
    
    def __init__(self):
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""
        pass
    
    async def handle(self, command: AsyncUpdateReadModelCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for update read model command: {command.command_id}")
        
        # Extract data from command
        aggregate_id = command.data["aggregate_id"]
        aggregate_type = command.data["aggregate_type"]
        snapshot = command.data["snapshot"]
        
        # Trigger Celery task
        task = update_read_model_task.delay(
            command_id=command.command_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            snapshot=snapshot
        )
        
        logger.info(f"Celery task triggered with task_id: {task.id} for command: {command.command_id}") 