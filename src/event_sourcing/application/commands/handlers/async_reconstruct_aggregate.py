from typing import Dict, Any
import logging

from pydantic_settings.main import T

from ..aggregate import AsyncReconstructAggregateCommand
from ...tasks.reconstruct_aggregate import reconstruct_aggregate_task

logger = logging.getLogger(__name__)


class AsyncReconstructAggregateCommandHandler:
    """Handler for asynchronously reconstructing aggregates via Celery"""
    
    def __init__(self):
        """Initialize the async handler (no dependencies needed as it just triggers Celery)"""
        pass
    
    async def handle(self, command: AsyncReconstructAggregateCommand) -> None:
        """Handle the async command by triggering a Celery task"""
        logger.info(f"Triggering Celery task for reconstruct aggregate command: {command.command_id}")
        
        # Extract data from command
        aggregate_id = command.data["aggregate_id"]
        aggregate_type = command.data["aggregate_type"]
        entity_name = command.data["entity_name"]
        
        # Trigger Celery task
        try:
            task = reconstruct_aggregate_task.delay(
            command_id=command.command_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            entity_name=entity_name
                )
            
            logger.info(f"Celery task triggered with task_id: {task.id} for command: {command.command_id}") 
        except Exception as e:
            logger.error(f"Error triggering Celery task: {e}")
            raise e